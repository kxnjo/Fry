from flask import Blueprint, render_template, request
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

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

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
    LIMIT %s OFFSET %s
    ''', (per_page, offset))
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

    return render_template("games/view_games.html", games = games, page = page)

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

    return render_template("games/game.html", game = game_data, categories = categories, developers = developers)

