import random

from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector
import config
from auth_utils import login_required  # persistent login
import random, datetime

from routes.game import view_game

# Create a Blueprint object
review_bp = Blueprint("review_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


@review_bp.route("/review-test")
@login_required
def get_reviews():
    conn = create_connection()
    cur = conn.cursor()

    # Retrieve selected game from the request
    selected_game = request.args.get('game')
    recommended = request.args.get('recommended')

    # user selected game AND tick 'recommended' checkbox
    if selected_game and recommended:
        sql_query = f'''
        SELECT 
            review.review_id, 
            review.review_text, 
            review.review_date, 
            user.username, 
            game.title,
            review.recommended
        FROM 
            review
        JOIN 
            user ON review.user_id = user.user_id
        JOIN 
            game ON review.game_id = game.game_id
        WHERE
            user.username IN (
                SELECT DISTINCT user.username
                FROM review
                JOIN user ON review.user_id = user.user_id
            ) AND (game.game_id = '{selected_game}') AND review.recommended = 'TRUE'
        ORDER BY
            review.review_date DESC
        LIMIT 10
        '''
    # user selected game but never tick 'recommended' checkbox
    elif selected_game:
        sql_query = f'''
        SELECT 
            review.review_id, 
            review.review_text, 
            review.review_date, 
            user.username, 
            game.title,
            review.recommended
        FROM 
            review
        JOIN 
            user ON review.user_id = user.user_id
        JOIN 
            game ON review.game_id = game.game_id
        WHERE
            user.username IN (
                SELECT DISTINCT user.username
                FROM review
                JOIN user ON review.user_id = user.user_id
            ) AND (game.game_id = '{selected_game}')
        ORDER BY
            review.review_date DESC
        LIMIT 10
        '''

    # default show all without filters
    else:
        sql_query = '''
        SELECT 
            review.review_id, 
            review.review_text, 
            review.review_date, 
            user.username, 
            game.title,
            review.recommended
        FROM 
            review
        JOIN 
            user ON review.user_id = user.user_id
        JOIN 
            game ON review.game_id = game.game_id
        WHERE
            user.username IN (
                SELECT DISTINCT user.username
                FROM review
                JOIN user ON review.user_id = user.user_id
            )
        ORDER BY
            RAND()
        LIMIT 10
        '''

    cur.execute(sql_query)

    # Fetch the review rows
    review_rows = cur.fetchall()

    # Create a list to hold review data
    reviews = []
    if review_rows:
        for row in review_rows:
            if row[5] == 'TRUE':
                recommended_val = "RECOMMENDED"
            else:
                recommended_val = "NOT RECOMMENDED"

            review_data = {
                "review_id": row[0],
                "review_text": row[1],
                "review_date": row[2],
                "user_id": row[3],
                "game_id": row[4],
                "recommended": recommended_val
            }
            reviews.append(review_data)

    # retrieve games from dropdown, sort by alphabetical order
    cur.execute('''
    SELECT 
        game_id, title 
    FROM 
        game
    ORDER BY
        title ASC
    ''')

    game_rows = cur.fetchall()
    games = []
    if game_rows:
        for row in game_rows:
            game_data = {
                "id": row[0],
                "title": row[1]
            }
            games.append(game_data)

    added_reviews_rows = cur.fetchall()
    user_reviews = []
    for row in added_reviews_rows:
        if row[4] == 'TRUE':
            recommended_val = 'RECOMMENDED'
        else:
            recommended_val = 'FALSE'
        added_reviews_data = {
            "review_id": row[0],
            "game_id": row[1],
            "review_date": row[2],
            "review_text": row[3],
            "recommended": recommended_val
        }
        user_reviews.append(added_reviews_data)
        print(user_reviews)
    # Close connection
    cur.close()
    conn.close()

    return render_template(
        "reviews/review.html",
        reviews=reviews,
        games=games,
        selected_game=selected_game,
        user_reviews=user_reviews
    )


def generate_review_id(existing_ids):
    while True:
        random_id = f"r{random.randint(1000000, 99999999)}"
        if random_id not in existing_ids:
            print(f'your id is now {random_id}')
            return random_id  # Return the unique ID


def xinhui():
    # Start connection
    print("starting xh")
    conn = create_connection()
    if conn is None:
        print("Failed to connect to database: Connection returned None")
        return "Failed to connect to database"

    try:
        cur = conn.cursor()

        # Show all reviews written by user
        cur.execute('''
                    SELECT r.review_id,g.game_id,g.title, r.review_date, r.review_text, r.recommended
                    FROM review r
                    JOIN game g ON r.game_id = g.game_id
                    WHERE r.user_id = %s
                    ORDER BY 
                    r.review_date DESC
                ''', (session['user_id'],))

        added_reviews_rows = cur.fetchall()
        if not added_reviews_rows:
            print("No reviews found for the user.")
            return []

        user_reviews = []
        for row in added_reviews_rows:
            if row[5] == 'TRUE':
                recommended_val = 'RECOMMENDED'
            else:
                recommended_val = 'NOT RECOMMENDED'
            added_reviews_data = {
                "review_id": row[0],
                "game_id": row[1],
                "game_title": row[2],
                "review_date": row[3],
                "review_text": row[4],
                "recommended": recommended_val
            }
            user_reviews.append(added_reviews_data)
            print("u r in here")

        return user_reviews

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"

    finally:
        if conn:
            conn.close()
        print("out of xinhui")


# @review_bp.route("/review-edit")
# def edit_reviews():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     review_id = request.args.get('review_id')
#     print("Review ID:", review_id)  # Debugging line
#     if review_id:
#         cur.execute('''
#         SELECT g.title, r.recommended, r.review_text
#         FROM game g, review r
#         WHERE r.game_id = g.game_id AND r.review_id = %s AND r.user_id = %s
#         ''', (review_id, session['user_id']))
#
#     review_info = cur.fetchone()
#
#     # retrieve games from dropdown, sort by alphabetical order
#     cur.execute('''
#     SELECT
#         game_id, title
#     FROM
#         game
#     ORDER BY
#         title ASC
#     ''')
#
#     game_rows = cur.fetchall()
#     games = []
#     if game_rows:
#         for row in game_rows:
#             game_data = {
#                 "id": row[0],
#                 "title": row[1]
#             }
#             games.append(game_data)
#
#     # Close connection
#     cur.close()
#     conn.close()
#
#     return render_template(
#         "reviews/review-edit.html",
#         # reviews=reviews,
#         games=games,
#         review_info=review_info,
#         review_id = review_id
#         # selected_game=selected_game
#     )

# @review_bp.route("/review-edit")
# @review_bp.route('/review-edit/<game_id>/<review_id>', methods=['GET', 'POST'])
# def edit_reviews(game_id, review_id=None):
#     conn = create_connection()
#     cur = conn.cursor()
#     selected_game = game_id
#     # review_id = request.args.get('review_id')
#     user_id = session.get('user_id')  # Get user_id from the session
#     print("Review ID:", review_id)  # Debugging line
#     print("User ID:", user_id)  # Debugging line
#
#     review_info = None  # Initialize to None
#
#     if review_id and user_id:
#         # If review_id is present, fetch the review information
#         cur.execute('''
#         SELECT g.title, r.recommended, r.review_text
#         FROM game g, review r
#         WHERE r.game_id = %s AND r.review_id = %s AND r.user_id = %s
#         ''', (selected_game, review_id, user_id))  # Wrapping the parameters in a tuple
#
#         review_info = cur.fetchone()  # Fetch the review info
#         print("Review Info:", review_info)  # Debugging line
#     else:
#         # If no review_id, prepare to add a new review
#         print("No review ID provided, ready to add a new review.")  # Debugging line
#
#     # Retrieve games from dropdown, sorted by alphabetical order
#     cur.execute('''
#     SELECT game_id, title
#     FROM game
#     WHERE game_id = %s
#     ORDER BY title ASC
#     ''', (selected_game,))  # Wrapping game_id in a tuple
#
#     game_rows = cur.fetchall()
#
#     games = []
#     if game_rows:
#         for row in game_rows:
#             game_data = {
#                 "id": row[0],
#                 "title": row[1]
#             }
#             games.append(game_data)
#
#     # Close connection
#     cur.close()
#     conn.close()
#
#     return render_template(
#         "reviews/review-edit.html",
#         games=games,
#         review_info=review_info,  # This will be None if adding a new review
#         review_id=review_id  # This will be None when adding a new review
#     )

@review_bp.route('/review-edit/<game_id>/<review_id>', methods=['GET', 'POST'])
@review_bp.route('/review-edit/<game_id>/', methods=['GET', 'POST'])
def edit_reviews(game_id, review_id=None):
    conn = create_connection()
    cur = conn.cursor()
    selected_game = game_id
    user_id = session.get('user_id')  # Get user_id from the session
    print("Review ID:", review_id)  # Debugging line
    print("User ID:", user_id)  # Debugging line
    print("selected game: ", selected_game)
    review_info = None  # Initialize to None

    # Always fetch the game title based on the game_id
    cur.execute(''' 
    SELECT title
    FROM game
    WHERE game_id = %s
    ''', (selected_game,))

    game_result = cur.fetchone()
    if game_result:
        game_title = game_result[0]

    # # Fixing the SQL query to fetch the game_id based on game title
    # cur.execute('''
    # SELECT game_id
    # FROM game
    # WHERE title = %s
    # ''', (game_id,))  # Pass game_id correctly as a tuple
    #
    # game_result = cur.fetchone()
    # selected_game = game_result[0]

    if review_id and user_id:
        # If review_id is present, fetch the review information
        cur.execute(''' 
        select r.review_id, g.title, r.recommended,r.review_text
        FROM review r
        JOIN game g ON g.game_id = r.game_id
        WHERE r.game_id = %s AND r.review_id = %s AND r.user_id = %s;
        ''', (selected_game, review_id, user_id))

        review_info = cur.fetchone()  # Fetch the review info
        print("Review Info:", review_info)  # Debugging line
    else:
        # If no review_id, prepare to add a new review
        print("No review ID provided, ready to add a new review.")  # Debugging line
    # # Retrieve games from dropdown, sorted by alphabetical order
    # cur.execute('''
    # SELECT game_id, title
    # FROM game
    # ORDER BY title ASC
    # ''')  # You don't need to filter by game_id here, unless you have a specific requirement.
    #
    # game_rows = cur.fetchall()  # Fetch all games
    #
    # games = []
    # if game_rows:
    #     for row in game_rows:
    #         game_data = {
    #             "id": row[0],
    #             "title": row[1]
    #         }
    #         games.append(game_data)

    # Close connection
    cur.close()
    conn.close()

    return render_template(
        "reviews/review-edit.html",
        selected_game = selected_game,
        game_title = game_title,
        review_info=review_info,  # This will be None if adding a new review
        review_id=review_id  # This will be None when adding a new review
    )


# def edit_reviews():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     review_id = request.args.get('review_id')
#     user_id = session.get('user_id')  # Get user_id from the session
#     print("Review ID:", review_id)  # Debugging line
#     print("User ID:", user_id)  # Debugging line
#
#     review_info = None  # Initialize to None
#
#     if review_id and user_id:
#         # If review_id is present, fetch the review information
#         cur.execute('''
#         SELECT g.title, r.recommended, r.review_text
#         FROM game g, review r
#         WHERE r.game_id = g.game_id AND r.review_id = %s AND r.user_id = %s
#         ''', (review_id, user_id))
#
#         review_info = cur.fetchone()  # Fetch the review info
#         print("Review Info:", review_info)  # Debugging line
#     else:
#         # If no review_id, prepare to add a new review
#         print("No review ID provided, ready to add a new review.")  # Debugging line
#
#     # Retrieve games from dropdown, sorted by alphabetical order
#     cur.execute('''
#     SELECT game_id, title
#     FROM game
#     ORDER BY title ASC
#     ''')
#     game_rows = cur.fetchall()
#
#     games = []
#     if game_rows:
#         for row in game_rows:
#             game_data = {
#                 "id": row[0],
#                 "title": row[1]
#             }
#             games.append(game_data)
#
#     # Close connection
#     cur.close()
#     conn.close()
#
#     return render_template(
#         "reviews/review-edit.html",
#         games=games,
#         review_info=review_info,  # This will be None if adding a new review
#         review_id=review_id  # This will be None when adding a new review
#     )


# @review_bp.route("review-add", methods=['GET'])
# def add_review():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     # Retrieve selected game from the request
#     selected_game = request.args.get('game')
#     recommended = request.args.get('recommended')
#     review_text = request.args.get('review-text')
#
#     review_id = request.args.get('review_id')
#
#     if recommended == "Recommended":
#         recommended_val = 'true'
#     else:
#         recommended_val = 'false'
#     print(f"this is ur game:{selected_game} ")
#     print(f"this is recommnded: {recommended}")
#     print(f"tihis is ur review texxt: {review_text}")
#     if review_id:
#         cur.execute('''
#         UPDATE
#         review
#         SET
#         recommended = %s , review_text = %s
#         WHERE
#         review_id= %s
#         ''', (recommended_val, review_text, review_id))
#
#     # done
#     else:
#         cur.execute(f'''
#         SELECT
#         review_id
#         FROM
#         review
#     ''')
#     id_rows = cur.fetchall()
#     existing_ids = []
#     for row in id_rows:
#         existing_ids.append(row[0])
#
#     generated_id = generate_review_id(existing_ids)
#     date = datetime.datetime.today().strftime("%Y-%m-%d")
#
#     cur.execute('''
#         INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
#         VALUES (%s, %s, %s, %s, %s, %s)
#     ''', (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
#
#     conn.commit()
#     return edit_reviews()


# @review_bp.route("review-add", methods=['GET'])
# def add_review():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     # Retrieve selected game from the request
#     selected_game = request.args.get('game')
#     recommended = request.args.get('recommended')
#     review_text = request.args.get('review-text')
#     review_id = request.args.get('review_id')
#
#     # Determine the recommended value
#     recommended_val = 'true' if recommended == "Recommended" else 'false'
#
#     print(f"this is ur game: {selected_game}")
#     print(f"this is recommended: {recommended}")
#     print(f"this is ur review text: {review_text}")
#     print(f"this is ur review id la: {review_id}")
#
#     if review_id:
#         # Update the review if review_id is present
#         cur.execute('''UPDATE review
#                        SET recommended = %s, review_text = %s
#                        WHERE review_id = %s''',
#                     (recommended_val, review_text, review_id))
#         print("i updated")
#     else:
#         # Get existing review IDs to generate a new review_id
#         cur.execute('SELECT review_id FROM review')
#         id_rows = cur.fetchall()
#         existing_ids = [row[0] for row in id_rows]
#
#         generated_id = generate_review_id(existing_ids)
#         date = datetime.datetime.today().strftime("%Y-%m-%d")
#
#         # Insert a new review
#         cur.execute('''INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
#                        VALUES (%s, %s, %s, %s, %s, %s)''',
#                     (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
#         print("i created new")
#     # Commit the changes
#     conn.commit()
#
#     # Redirect to the edit reviews page after the operation
#     return redirect(url_for('review_bp.edit_reviews', review_id=review_id or generated_id))

def get_id_existence(cur, review_id):
    # Execute the SQL query to check if the review_id exists
    cur.execute('''
    SELECT COUNT(*)
    FROM review
    WHERE review_id = %s
    ''', (review_id,))  # Pass the review_id as a parameter to prevent SQL injection

    # Fetch the result
    count = cur.fetchone()[0]

    # Return True if the count is greater than 0, meaning the ID exists
    return count > 0


# # INSERT/UPDATE REVIEW
# @review_bp.route("review-add", methods=['GET'])
# def add_review():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     # Retrieve selected game from the request
#     selected_game = request.args.get('game')
#     recommended = request.args.get('recommended')
#     review_text = request.args.get('review-text')
#     # review_id = request.args.get('review_id')  # Should be None for new reviews
#     review_id = request.args.get('review_id') if request.args.get(
#         'review_id') != "None" else None  # Should be None for new reviews
#
#     # Determine the recommended value
#     recommended_val = 'TRUE' if recommended == "Recommended" else 'FALSE'
#
#     print(f"Selected game: {selected_game}")
#     print(f"Recommended: {recommended}")
#     print(f"Review text: {review_text}")
#     print(f"Review ID (should be None for new review): {review_id}")
#
#     # if review_id is None:  # This check is to update existing review
#     id_check = get_id_existence(cur, review_id)
#     # WHY DOES if review_id: NOT WORK @ xh, u can try to use if review_id, it doesnt work
#     # if review_id:
#     if id_check:
#         print("i found ID !")
#         cur.execute('''UPDATE review
#                        SET recommended = %s, review_text = %s
#                        WHERE review_id = %s''',
#                     (recommended_val, review_text, review_id))
#         print("Updated existing review")
#
#     else:
#         print("i need create new id !")
#         # Get existing review IDs to generate a new review_id
#         cur.execute('SELECT review_id FROM review')
#         id_rows = cur.fetchall()
#         existing_ids = [row[0] for row in id_rows]
#
#         generated_id = generate_review_id(existing_ids)  # Generate new ID
#         print(f"Generated new review ID: {generated_id}")
#         date = datetime.datetime.today().strftime("%Y-%m-%d")
#
#         # Insert a new review
#         cur.execute('''INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
#                        VALUES (%s, %s, %s, %s, %s, %s)''',
#                     (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
#         print(f"Created new review with ID: {generated_id}")
#
#     # Commit the changes
#     conn.commit()
#
#     # Redirect to the edit reviews page with the new review ID
#     return redirect(url_for('review_bp.get_reviews'))

@review_bp.route('/review-add', methods=['POST'])
@review_bp.route('review-add/<review_id>', methods=['POST'])
def add_review(review_id=None):
    conn = create_connection()
    cur = conn.cursor()

    # Retrieve selected game and review data from the POST request
    # selected_game = request.form['game']  # Direct access
    selected_game = request.form['game_id']  # This will contain the game ID
    # print(request.form)  # Check what is being submitted

    # return "hello"
    # # Fixing the SQL query to fetch the game_id based on game title
    # cur.execute('''
    # SELECT game_id
    # FROM game
    # WHERE title = %s
    # ''', (selected_game,))  # Pass game_id correctly as a tuple
    #
    # game_result = cur.fetchone()
    # selected_game = game_result[0]
    recommended = request.form['recommended']
    review_text = request.form['review_text']
    # review_id = request.form['review_id'] if request.form['review_id'] != "None" else None

    # Determine the recommended value
    recommended_val = 'TRUE' if recommended == "Recommended" else 'FALSE'

    # print(f"Selected game: {selected_game}")
    print(f"Recommended: {recommended}")
    print(f"Review text: {review_text}")
    print(f"ur review game: {selected_game}")
    print(f"Review ID (should be None for new review): {review_id}")

    id_check = get_id_existence(cur, review_id)

    if id_check:
        print("Found ID!")
        cur.execute('''UPDATE review
                       SET recommended = %s, review_text = %s
                       WHERE review_id = %s''',
                    (recommended_val, review_text, review_id))
        print("Updated existing review")

    else:
        print("Creating new ID!")
        # Get existing review IDs to generate a new review_id
        cur.execute('SELECT review_id FROM review')
        id_rows = cur.fetchall()
        existing_ids = [row[0] for row in id_rows]

        generated_id = generate_review_id(existing_ids)  # Generate new ID
        print(f"Generated new review ID: {generated_id}")
        date = datetime.datetime.today().strftime("%Y-%m-%d")

        # Insert a new review
        cur.execute('''INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
                       VALUES (%s, %s, %s, %s, %s, %s)''',
                    (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
        print(f"Created new review with ID: {generated_id}")
        pass

    # Commit the changes
    conn.commit()
    # Ensure selected_game has no leading/trailing spaces
    selected_game = selected_game.strip()

    # Redirect to the edit reviews page with the new review ID
    # return redirect(url_for('review_bp.get_reviews'))
    return redirect(url_for('game_bp.view_game', game_id=selected_game))


# Delete Review
# @review_bp.route("review-delete/<review_id>", methods=['GET'])
@review_bp.route("review-delete/<review_id>")
def delete_review(review_id):
    conn = create_connection()
    cur = conn.cursor()
    # review_id = request.args.get('review_id')  # Should be None for new reviews
    if review_id:
        cur.execute('''
        DELETE FROM
        review
        WHERE
        review_id = %s
        ''', (review_id,))
    print("doned")
    conn.commit()
    return redirect(url_for('user_bp.dashboard'))

### OLD
# INSERT/UPDATE REVIEW
# @review_bp.route("review-add", methods=['GET'])
# def add_review_old():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     # Retrieve selected game from the request
#     selected_game = request.args.get('game')
#     recommended = request.args.get('recommended')
#     review_text = request.args.get('review-text')
#     # review_id = request.args.get('review_id')  # Should be None for new reviews
#     review_id = request.args.get('review_id') if request.args.get(
#         'review_id') != "None" else None  # Should be None for new reviews
#
#     # Determine the recommended value
#     recommended_val = 'TRUE' if recommended == "Recommended" else 'FALSE'
#
#     print(f"Selected game: {selected_game}")
#     print(f"Recommended: {recommended}")
#     print(f"Review text: {review_text}")
#     print(f"Review ID (should be None for new review): {review_id}")
#
#     # if review_id is None:  # This check is to update existing review
#     id_check = get_id_existence(cur, review_id)
#     # WHY DOES if review_id: NOT WORK @ xh, u can try to use if review_id, it doesnt work
#     # if review_id:
#     if id_check:
#         print("i found ID !")
#         cur.execute('''UPDATE review
#                        SET recommended = %s, review_text = %s
#                        WHERE review_id = %s''',
#                     (recommended_val, review_text, review_id))
#         print("Updated existing review")
#
#     else:
#         print("i need create new id !")
#         # Get existing review IDs to generate a new review_id
#         cur.execute('SELECT review_id FROM review')
#         id_rows = cur.fetchall()
#         existing_ids = [row[0] for row in id_rows]
#
#         generated_id = generate_review_id(existing_ids)  # Generate new ID
#         print(f"Generated new review ID: {generated_id}")
#         date = datetime.datetime.today().strftime("%Y-%m-%d")
#
#         # Insert a new review
#         cur.execute('''INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
#                        VALUES (%s, %s, %s, %s, %s, %s)''',
#                     (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
#         print(f"Created new review with ID: {generated_id}")
#
#     # Commit the changes
#     conn.commit()
#
#     # Redirect to the edit reviews page with the new review ID
#     return redirect(url_for('review_bp.get_reviews'))


# @review_bp.route("/review-edit")
# def edit_reviews():
#     conn = create_connection()
#     cur = conn.cursor()
#
#     review_id = request.args.get('review_id')
#     user_id = session.get('user_id')  # Get user_id from the session
#     print("Review ID:", review_id)  # Debugging line
#     print("User ID:", user_id)  # Debugging line
#
#     review_info = None  # Initialize to None
#
#     if review_id and user_id:
#         # If review_id is present, fetch the review information
#         cur.execute('''
#         SELECT g.title, r.recommended, r.review_text
#         FROM game g, review r
#         WHERE r.game_id = g.game_id AND r.review_id = %s AND r.user_id = %s
#         ''', (review_id, user_id))
#
#         review_info = cur.fetchone()  # Fetch the review info
#         print("Review Info:", review_info)  # Debugging line
#     else:
#         # If no review_id, prepare to add a new review
#         print("No review ID provided, ready to add a new review.")  # Debugging line
#
#     # Retrieve games from dropdown, sorted by alphabetical order
#     cur.execute('''
#     SELECT game_id, title
#     FROM game
#     ORDER BY title ASC
#     ''')
#     game_rows = cur.fetchall()
#
#     games = []
#     if game_rows:
#         for row in game_rows:
#             game_data = {
#                 "id": row[0],
#                 "title": row[1]
#             }
#             games.append(game_data)
#
#     # Close connection
#     cur.close()
#     conn.close()
#
#     return render_template(
#         "reviews/review-edit.html",
#         games=games,
#         review_info=review_info,  # This will be None if adding a new review
#         review_id=review_id  # This will be None when adding a new review
#     )
