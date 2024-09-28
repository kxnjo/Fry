from flask import Blueprint, render_template
import mysql.connector
import config

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
def check():
    conn = create_connection()
    cur = conn.cursor()
    #     cur.execute('''
    # SELECT
    #     review.review_id,
    #     review.review_text,
    #     review.review_date,
    #     user.username,
    #     game.title
    # FROM
    #     review
    # JOIN
    #     user ON review.user_id = user.user_id
    # JOIN
    #     game ON review.game_id = game.game_id
    # GROUP BY
    #     user.username
    # ORDER BY
    #     RAND()
    # LIMIT 10
    #         ''')

    # Show 10 random reviews distinct users
    cur.execute('''
SELECT 
    review.review_id, 
    review.review_text, 
    review.review_date, 
    user.username, 
    game.title
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
    ''')
    rows = cur.fetchall()

    # Create a list to hold review data
    reviews = []
    if rows:
        for row in rows:
            review_data = {
                "review_id": row[0],
                "review_text": row[1],
                "review_date": row[2],
                "user_id": row[3],
                "game_id": row[4]
            }
            reviews.append(review_data)
    else:
        print("not found")

    return render_template("reviews/review.html", reviews=reviews)
