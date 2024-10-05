from flask import Blueprint, render_template, request, session
import mysql.connector
import config

# Create a Blueprint object
game_bp = Blueprint("game_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


@game_bp.route("/games")
def view_all_games():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'title')  # Default sort is by title
    sort_order = request.args.get('order', 'asc')  # Default order is ascending

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    if sort_by == 'price':
        order_by = 'g.price'
    elif sort_by == 'release_date':
        order_by = 'g.release_date'
    else:
        order_by = 'g.title'  # Default is alphabetically by title

    order_direction = 'ASC' if sort_order == 'asc' else 'DESC'

    query = f'''
    SELECT 
        g.game_id,
        g.title,
        g.release_date,
        g.price
    FROM 
        game g
    ORDER BY 
        {order_by} {order_direction}
    LIMIT %s OFFSET %s
    '''

    conn = create_connection()
    cur = conn.cursor()

    # Execute the query with the limit and offset parameters
    cur.execute(query, (per_page, offset))
    rows = cur.fetchall()

    # Create a list to hold game data
    games = []
    if rows:
        for row in rows:
            game_data = {
                "game_id": row[0],
                "game_title": row[1],
                "game_release_date": row[2],
                "game_price": row[3]
            }
            games.append(game_data)
    else:
        print("not found")

    return render_template("games/view_games.html", games=games, page=page, sort_by=sort_by, sort_order=sort_order)


@game_bp.route("/game/<game_id>")
def view_game(game_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT 
        g.game_id,
        g.title,
        g.release_date,
        g.price
    FROM 
        game g
    WHERE 
        g.game_id = %s
    LIMIT 1;
    ''', (game_id,))
    game = cur.fetchone()

    if not game:
        return "Game not found", 404

    game_data = {
        "game_id": game[0],
        "game_title": game[1],
        "game_release_date": game[2],
        "game_price": game[3]
    }

    cur.execute('''
    SELECT 
        c.category_id, c.category_name
    FROM 
        category c
    JOIN 
        game_category gc 
    ON 
        c.category_id = gc.category_id
    WHERE 
        gc.game_id = %s
    ;
    ''', (game_id,))
    rows = cur.fetchall()

    categories = []
    if rows:
        for row in rows:
            category = {
                "category_id": row[0],
                "category_name": row[1],
            }
            categories.append(category)
    else:
        print("not found")

    cur.execute('''
    SELECT 
        d.developer_id, d.developer_name
    FROM 
        developer d
    JOIN 
        game_developer gd 
    ON 
        d.developer_id = gd.developer_id
    WHERE 
        gd.game_id = %s
    ;
    ''', (game_id,))
    rows = cur.fetchall()

    developers = []
    if rows:
        for row in rows:
            developer = {
                "developer_id": row[0],
                "developer_name": row[1],
            }
            developers.append(developer)
    else:
        print("not found")


    # Retrieve Reviews from DB
    cur.execute('''
        SELECT
            r.review_id, r.review_text, r.review_date, u.username, g.title, r.recommended
        FROM
            review r
        JOIN user u ON r.user_id = u.user_id
        JOIN game g ON r.game_id = g.game_id
        WHERE
            g.game_id = %s
        ORDER BY
            r.review_date DESC
        LIMIT 10
    ''', (game_id,))

    # Create a list to hold review data
    reviews = []

    # Fetch the review rows
    review_rows = cur.fetchall()
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

    # count number of recommended / non recommended reviews per game
    cur.execute('''
        SELECT 
            SUM(review.recommended = 'TRUE') AS true_count,
            SUM(review.recommended = 'FALSE') AS false_count
        FROM 
            review
        WHERE 
            review.game_id = %s
    ''', (game_id,))

    recommended_rows = cur.fetchone()
    if recommended_rows:
        true_count = recommended_rows[0]
        false_count = recommended_rows[1]
        # After fetching the recommended counts
        recommended_data = {
            "true_count": true_count,
            "false_count": false_count
        }
        
    # Check if the game is already in the user's wishlist
    user_id = session['user_id']
    check_wishlist_query = """
        SELECT * FROM wanted_game 
        WHERE user_id = %s AND game_id = %s
    """
    cur.execute(check_wishlist_query, (user_id, game_id))
    result = cur.fetchone()

    # If result is not None, the game is already in the wishlist
    gameInWishlist = result is not None

    return render_template("games/game.html", game=game_data, categories=categories, developers=developers,
                           reviews=reviews, recommended_data = recommended_data, gameInWishlist=gameInWishlist)
