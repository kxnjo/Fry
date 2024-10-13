from flask import Blueprint, render_template, request
import mysql.connector
import config

# Create a Blueprint object
developer_bp = Blueprint("developer_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

# route to view all developers page
@developer_bp.route("/developers")
def view_all_developers():

    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT 
        d.developer_id,
        d.developer_name
    FROM 
        developer d
    LIMIT %s OFFSET %s
    ''', (per_page, offset))
    rows = cur.fetchall()

    # Create a list to hold game data
    developers = []
    if rows:
        for row in rows:
            developer_data = {
                "developer_id": row[0],
                "developer_name": row[1],
            }
            developers.append(developer_data)
    else:
        print("not found")

    return render_template("developers/view_developers.html", developers = developers, page = page)

# route to view individual developer page
@developer_bp.route("/developer/<developer_id>")
def view_developer(developer_id):

    # query to select specific developer
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT 
        g.game_id, g.title, d.developer_name
    FROM 
        game g
    JOIN 
        game_developer gd
    ON 
        g.game_id = gd.game_id
    JOIN 
        developer d
    ON 
        d.developer_id = gd.developer_id
    WHERE 
        gd.developer_id = %s;
    ''', (developer_id,))
    rows = cur.fetchall()

    games = []
    if rows:
        for row in rows:
            game_data = {
                "game_id": row[0], 
                "game_title": row[1],   
                "developer_name": row[2],
            }
            games.append(game_data)
            
    else:
        print("not found")

    return render_template("developers/developer.html", games = games)

