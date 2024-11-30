from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector

from dotenv import load_dotenv
import os

load_dotenv('config.env')
from auth_utils import login_required  # persistent login
import random, datetime

# mongo
from mongo_cfg import get_NoSQLdb
# Create a Blueprint object
review_bp = Blueprint("review_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_DATABASE"),
    )

@review_bp.route('/test-db-connection')
def mongo_connection():
    #
    # db = get_NoSQLdb()
    # get_reviews = db.new_game.find({"reviews": 1})
    #
    # print(get_reviews)
    db = get_NoSQLdb()

    # Correct way to query MongoDB for specific fields
    # Use projection to get only the "reviews" field
    get_reviews = db.new_game.find({}, {"reviews": 1})

    # Convert the MongoDB cursor to a list and print the result
    reviews_list = list(get_reviews)  # Convert cursor to list to retrieve all documents
    print(reviews_list)  # This will print the reviews in the terminal/log

    return {"reviews": reviews_list}  # Return the reviews in the response (JSON)
    # if db is None:
    #     return "Database not initialized!!.", 500
    # try:
    #     collections = db.list_collection_names()
    #     return f"Successfully connected to MongoDB. Collections: {collections}", 200
    # except Exception as e:
    #     return f"Failed to connect to MongoDB: {e}", 500


@review_bp.route("/mongo-test", methods =["GET"])
def mongo_test():
    selected_game = request.args.get("game") # returns game_id from selected dropdown
    recommended = request.args.get("recommended")

    # Use str() to safely convert None to an empty string
    print("Selected value: " + (selected_game if selected_game is not None else "None"))
    print("Recommended value: " + (recommended if recommended is not None else "None"))

    filter_query = {}
    if selected_game:
        filter_query["_id"] = selected_game
    if recommended:
        filter_query["reviews.recommended"] = True

    db = get_NoSQLdb()
    user_id = session.get('_id')
    user_written_reviews(user_id)

    # Fetch all games to populate the dropdown
    all_games = db.new_game.find({}, {"_id": 1, "title": 1})  # Query for all games

    # Fetch game reviews based on filter criteria
    all_game_reviews = db.new_game.find(filter_query, {"reviews": 1, "title": 1, "_id": 1})

    # Create a list to hold review data
    reviews = []
    games = []

    for doc in all_games:
        games.append({
            "id": doc["_id"],
            "title": doc["title"]
        })

    for doc in all_game_reviews:
        games_data = {
            "id": doc["_id"],
            "title": doc["title"]
        }
        games.append(games_data)

        for review in doc["reviews"]:
            # Extract review details, assuming review is a dictionary
            if not recommended or review.get("recommended", False):  # Apply 'recommended' filter manually
                review_data = {
                    "game_title": doc["title"],
                    "review_date": review["review_date"],
                    "user_id": review["user_id"],
                    "recommended": review["recommended"],
                    "review_text": review["review_text"]
                }
                reviews.append(review_data)

    return render_template(
        "reviews/review-mongo.html",
        reviews=reviews,
        games=games,
        selected_game=selected_game,
        recommended=recommended
    )

@review_bp.route('/review-add', methods=['POST'])
# @review_bp.route('review-add/<review_id>', methods=['POST'])
def mongo_add(review_id=None):
    db = get_NoSQLdb()
    user_id = session.get('_id')

    # Retrieve selected game and review data from the POST request
    selected_game = request.form['game_id']  # This will contain the game ID
    recommended = request.form['recommended']  # contain the recommended value
    review_text = request.form['review_text']  # contain the review_text content
    print("mongo_add g_id : " + selected_game)
    print("mongo recommended: " + recommended)
    print("mongo review_Text: " + review_text)

    source = request.form['source']
    source = "dashboard"
    # Determine the recommended value
    recommended_val = True if recommended == "Recommended" else False


    review_check = mongo_find_review(user_id,selected_game)
    if review_check:
        # The review exists, so we will update it
        update_review = {
            '$set': {
                'reviews.$.review_text': review_text,  # Update the review_text of the matched review
                'reviews.$.recommended': recommended_val  # Update the recommended value
            }
        }

        # Update the review in the database
        db.new_game.update_one(
            {'_id': selected_game, 'reviews.user_id': user_id},  # Find the game and review by user_id
            update_review  # Apply the update
        )
    else: # ITS NEW
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        new_review = {
            'review_text': review_text,
            'date': date,
            'user_id': user_id,
            'recommended': recommended_val
        }

        # Insert the new review into the 'reviews' array
        db.new_game.update_one(
            {'_id': selected_game},  # Find the game by game_id
            {'$push': {'reviews': new_review}}  # Append the new review to the reviews array
        )


    # if id_check:
    #     # Review ID exists in the database, update accordingly
    #     cur.execute('''
    #                 UPDATE
    #                     review
    #                 SET
    #                     recommended = %s, review_text = %s
    #                 WHERE
    #                     review_id = %s''',
    #                 (recommended_val, review_text, review_id))
    #
    # else:
    #     # Get existing review IDs to generate a new review_id
    #     cur.execute('SELECT review_id FROM review')
    #     id_rows = cur.fetchall()
    #     existing_ids = [row[0] for row in id_rows]
    #
    #     generated_id = generate_review_id(existing_ids)  # Generate new ID
    #     print(f"Generated new review ID: {generated_id}")
    #     date = datetime.datetime.today().strftime("%Y-%m-%d")
    #
    #     # Insert a new review
    #     cur.execute('''INSERT INTO review (review_id, review_text, review_date, user_id, game_id, recommended)
    #                    VALUES (%s, %s, %s, %s, %s, %s)''',
    #                 (generated_id, review_text, date, session['user_id'], selected_game, recommended_val))
    #     pass
    #
    # # # Commit the changes
    # conn.commit()
    # # Ensure selected_game has no leading/trailing spaces
    # selected_game = selected_game.strip()

    # Redirect based on the source
    if source == 'dashboard':
        return redirect(url_for('user_bp.dashboard'))
    else:
        return redirect(url_for('game_bp.view_game', game_id=selected_game))


def mongo_find_review(user_id, game_id):
    # Get the database
    db = get_NoSQLdb()

    # Find the game by game_id and user_id
    result = db.new_game.find(
        {
            "_id": game_id,  # Match the game_id to the _id field
            "reviews": {"$elemMatch": {"user_id": user_id}}  # Match the user_id inside reviews
        },
        {"title": 1, "reviews.$": 1}  # Projection to return only title and matched review
    )
    # Return the result
    return result

@review_bp.route("/mongo-add")
def mongo_edit():
    return render_template('reviews/review-edit.html')

# @review_bp.route('/review-edit/<game_id>/<review_id>', methods=['GET', 'POST'])
@review_bp.route('/mongo-edit/<game_id>/', methods=['GET', 'POST'])
def edit_reviews(game_id):

    db = get_NoSQLdb()
    selected_game = game_id
    user_id = session.get('user_id')  # Get user_id from the session

    review_info = None  # Initialize to None
    game_title = db.new_game.find_one(
        {
            "_id": game_id,  # Match the game_id to the _id field
        },
        {"title": 1}  # Projection to return only title and matched review
    )
    if game_title:
        title = game_title['title']
    # Get the title from the document and print it
        print("This is game_title: " + title)
    # # Always fetch the game title based on the game_id
    # cur.execute('''
    # SELECT title
    # FROM game
    # WHERE game_id = %s
    # ''', (selected_game,))
    #
    # game_result = cur.fetchone()
    # if game_result:
    #     game_title = game_result[0]
    #
    # if review_id and user_id:
    #     # If review_id is present, fetch the review information
    #     cur.execute('''
    #     SELECT
    #         r.review_id, g.title, r.recommended,r.review_text
    #     FROM
    #         review r
    #     JOIN
    #         game g ON g.game_id = r.game_id
    #     WHERE
    #         r.game_id = %s AND r.review_id = %s AND r.user_id = %s;
    #     ''', (selected_game, review_id, user_id))
    #
    #     review_info = cur.fetchone()  # Fetch the review info
    # else:
    #     # If no review_id, prepare to add a new review
    #     print("No review ID provided, ready to add a new review.")  # Debugging line
    #
    # # Close connection
    # cur.close()
    # conn.close()

    return render_template(
        "reviews/review-edit-mongo.html",
        selected_game = selected_game,
        game_title = title,
        review_info=review_info,  # This will be None if adding a new review
    )
@review_bp.route("/review-test")
def get_reviews():
    # Get the current page and filter parameters from the request
    page = request.args.get("page", 1, type=int)
    selected_game = request.args.get("game")
    recommended = request.args.get("recommended")

    total_reviews_count = getReviewsNum(selected_game,recommended)
    # Get total number of pages required
    reviews_per_page = 10
    total_pages_required = (total_reviews_count // reviews_per_page) + 1

    start = (page - 1) * reviews_per_page
    end = start + reviews_per_page

    # Get filtered reviews
    all_reviews = getReviewList(start, end, selected_game, recommended)

    conn = create_connection()
    cur = conn.cursor(buffered=True)

    # Retrieve games from dropdown, sorted alphabetically
    cur.execute('''
    SELECT game_id, title
    FROM game
    ORDER BY title ASC
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

    return render_template(
        "reviews/review.html",
        reviews=all_reviews,
        page=page,
        total_pages=total_pages_required,
        games=games,
        selected_game=selected_game,
        recommended=recommended,
    )

def getReviewsNum(selected_game=None,recommended=None):
    conn = create_connection()
    cur = conn.cursor(buffered=True)
    query = '''
        SELECT COUNT(*) as total_rows
        FROM review
    '''
    params = []
    if selected_game and recommended:
        query += "WHERE game_id = %s AND recommended ='TRUE'"
        params.append(selected_game)
    elif selected_game:
        query += "WHERE game_id = %s"
        params.append(selected_game)
    elif recommended:
        query += "WHERE recommended = 'TRUE'"

    if selected_game or recommended:
        cur.execute(query,tuple(params))
    else:
        cur.execute(query)

    total_reviews_count = cur.fetchone()

    exact_count = total_reviews_count[0] # return exact number of rows from the query

    cur.close()
    conn.close()

    return exact_count

def getReviewList(start=0, end=10, game=None, recommended=None):
    conn = create_connection()
    cur = conn.cursor(buffered=True)

    # Base query
    query = '''
    SELECT * FROM (
        SELECT 
        g.title, r.review_date, u.username, r.recommended, r.review_text, ROW_NUMBER() OVER (ORDER BY r.review_id) as row_num 
        FROM 
        review r 
        JOIN game g ON r.game_id = g.game_id 
        JOIN user u ON r.user_id = u.user_id
    '''

    # Add game filter if selected
    if game:
        query += " WHERE r.game_id = %s"
        params = [game]

    # If filter not selected
    if not game:
        params = []

    # Add recommended filter if checked
    if recommended:
        query += " AND r.recommended = 'TRUE'"

    # Complete the subquery
    query += ") as temp_table WHERE row_num > %s AND row_num <= %s"
    params += [start, end]

    cur.execute(query, params)

    all_reviews_data = cur.fetchall()

    cur.close()
    conn.close()

    # Create a list to hold review data
    reviews = []
    if all_reviews_data:
        for row in all_reviews_data:
            review_data = {
                "game_title": row[0],
                "review_date": row[1],
                "user_id": row[2],
                "recommended": row[3],
                "review_text": row[4]
            }
            reviews.append(review_data)

    return reviews

def get_games_with_reviews():
    conn = create_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT
        g.title
    FROM
        game g
    JOIN
        review r ON g.game_id = r.game_id
    GROUP BY
        g.game_id, g.title
    HAVING
        COUNT(r.game_id) >= 1
    ORDER BY
    title ASC
    ''')

    get_game_count = cur.fetchall()
    game_with_reviews = []
    if get_game_count:
        for row in get_game_count:
            game_reviews = {
                'title': row[0],
            }
            game_with_reviews.append(game_reviews)

    return game_with_reviews

def generate_review_id(existing_ids):
    while True:
        # generate a new review_id
        random_id = f"r{random.randint(1000000, 99999999)}"
        if random_id not in existing_ids:
            return random_id  # Return the unique ID


def user_written_reviews(user_id):
    # Start connection
    db = get_NoSQLdb()
    # Find the game by game_id and user_id
    user_reviews = db.new_game.find(
        {
            "reviews": {"$elemMatch": {"user_id": user_id}}  # Match the user_id inside reviews
        },
        {"title": 1, "reviews.$": 1}  # Projection to return only title and matched review
    )

    # Convert cursor to list and print to inspect the results
    reviews = []

    # Convert the cursor to a list and check if we found any reviews
    user_reviews_list = list(user_reviews)
    if user_reviews_list:
        for game in user_reviews_list:
            for user_review in game['reviews']:
                if user_review["user_id"] == user_id:  # Confirm it's the review for the correct user
                    review_data = {
                        "game_title": game["title"],
                        "review_date": user_review["review_date"],
                        "user_id": user_review["user_id"],
                        "recommended": user_review["recommended"],
                        "review_text": user_review["review_text"]
                    }
                    reviews.append(review_data)
    else:
        print(f"No reviews found for user_id: {user_id}")
    print("reviews here")
    print(reviews)
    return reviews  # Return the list of reviews for the user


    # db.new_game.find()
    # conn = create_connection()
    # if conn is None:
    #     print("Failed to connect to database: Connection returned None")
    #     return "Failed to connect to database"
    #
    # try:
    #     cur = conn.cursor()
    #
    #     # Show all reviews written by user
    #     cur.execute('''
    #                 SELECT
    #                     r.review_id,g.game_id,g.title, r.review_date, r.review_text, r.recommended
    #                 FROM
    #                     review r
    #                 JOIN
    #                     game g ON r.game_id = g.game_id
    #                 WHERE
    #                     r.user_id = %s
    #                 ORDER BY
    #                     r.review_date DESC
    #             ''', (user_id,))
    #
    #     added_reviews_rows = cur.fetchall()
    #     if not added_reviews_rows:
    #         # if no written_reviews found, return []
    #         return []
    #
    #     user_reviews = []
    #     for row in added_reviews_rows:
    #         # if the row's recommended value = 'TRUE', set to 'RECOMMENDED'
    #         if row[5] == 'TRUE':
    #             recommended_val = 'RECOMMENDED'
    #         else:
    #             recommended_val = 'NOT RECOMMENDED'
    #         added_reviews_data = {
    #             "review_id": row[0],
    #             "game_id": row[1],
    #             "game_title": row[2],
    #             "review_date": row[3],
    #             "review_text": row[4],
    #             "recommended": recommended_val
    #         }
    #         user_reviews.append(added_reviews_data)
    #
    #     return user_reviews
    #
    # except Exception as e:
    #     print(f"An error occurred: {str(e)}")
    #     return f"An error occurred: {str(e)}"
    #
    # finally:
    #     if conn:
    #         conn.close()

# @review_bp.route('/review-edit/<game_id>/<review_id>', methods=['GET', 'POST'])
# @review_bp.route('/review-edit/<game_id>/', methods=['GET', 'POST'])
# def edit_reviews(game_id, review_id=None):
#     conn = create_connection()
#     cur = conn.cursor()
#     selected_game = game_id
#     user_id = session.get('user_id')  # Get user_id from the session
#
#     review_info = None  # Initialize to None
#
#     # Always fetch the game title based on the game_id
#     cur.execute('''
#     SELECT title
#     FROM game
#     WHERE game_id = %s
#     ''', (selected_game,))
#
#     game_result = cur.fetchone()
#     if game_result:
#         game_title = game_result[0]
#
#     if review_id and user_id:
#         # If review_id is present, fetch the review information
#         cur.execute('''
#         SELECT
#             r.review_id, g.title, r.recommended,r.review_text
#         FROM
#             review r
#         JOIN
#             game g ON g.game_id = r.game_id
#         WHERE
#             r.game_id = %s AND r.review_id = %s AND r.user_id = %s;
#         ''', (selected_game, review_id, user_id))
#
#         review_info = cur.fetchone()  # Fetch the review info
#     else:
#         # If no review_id, prepare to add a new review
#         print("No review ID provided, ready to add a new review.")  # Debugging line
#
#     # Close connection
#     cur.close()
#     conn.close()
#
#     return render_template(
#         "reviews/review-edit.html",
#         selected_game = selected_game,
#         game_title = game_title,
#         review_info=review_info,  # This will be None if adding a new review
#         review_id=review_id  # This will be None when adding a new review
#     )

def get_id_existence(cur, review_id): # this function will be called in add_review()
    # Check if the review_id exists
    cur.execute('''
    SELECT COUNT(*)
    FROM review
    WHERE review_id = %s
    ''', (review_id,))

    # Fetch the result
    count = cur.fetchone()[0]

    # Return True if the count is greater than 0, meaning the ID exists
    return count > 0

# allow for both routes with and without review_id to execute the add_review() function
# # used for both UPDATE and INSERT into review table
# @review_bp.route('/review-add', methods=['POST'])
# @review_bp.route('review-add/<review_id>', methods=['POST'])
# def add_review(review_id=None):
#     conn = create_connection()
#     cur = conn.cursor()
#
#     # Retrieve selected game and review data from the POST request
#     selected_game = request.form['game_id']  # This will contain the game ID
#     recommended = request.form['recommended'] # contain the recommended value
#     review_text = request.form['review_text'] # contain the review_text content
#
#     source = request.form['source']
#     # Determine the recommended value
#     recommended_val = 'TRUE' if recommended == "Recommended" else 'FALSE'
#
#     # Check if the review_id passed in exists in the database
#     id_check = get_id_existence(cur, review_id)
#
#     if id_check:
#     # Review ID exists in the database, update accordingly
#         cur.execute('''
#                     UPDATE
#                         review
#                     SET
#                         recommended = %s, review_text = %s
#                     WHERE
#                         review_id = %s''',
#                     (recommended_val, review_text, review_id))
#
#     else:
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
#         pass
#
#     # Commit the changes
#     conn.commit()
#     # Ensure selected_game has no leading/trailing spaces
#     selected_game = selected_game.strip()
#
#     # Redirect based on the source
#     if source == 'dashboard':
#         return redirect(url_for('user_bp.dashboard'))
#     else:
#         return redirect(url_for('game_bp.view_game', game_id=selected_game))


# Delete Review
# @review_bp.route("review-delete/<review_id>", methods=['GET'])
@review_bp.route("review-delete/<review_id>", methods=['GET'])
def delete_review(review_id):
    conn = create_connection()
    cur = conn.cursor()

    # Retrieve game_id and source from URL query parameters
    game_id = request.args.get('game_id')
    source = request.args.get('source')

    if review_id:
        cur.execute('''
        DELETE FROM
        review
        WHERE
        review_id = %s
        ''', (review_id,))

    conn.commit()

    # Redirect based on the source
    if source == 'dashboard':
        return redirect(url_for('user_bp.dashboard'))
    else:
        return redirect(url_for('game_bp.view_game', game_id=game_id))

