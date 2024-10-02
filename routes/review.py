from flask import Blueprint, render_template, request
import mysql.connector
import config
from auth_utils import login_required  # persistent login

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
def check():
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

    # Close connection
    cur.close()
    conn.close()

    return render_template(
        "reviews/review.html",
        reviews=reviews,
        games=games,
        selected_game=selected_game
    )
