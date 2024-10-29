from flask import Blueprint, render_template, request
import mysql.connector

from dotenv import load_dotenv
import os

load_dotenv('config.env')

# Create a Blueprint object
category_bp = Blueprint("category_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_DATABASE"),
    )

# route to view all categories
@category_bp.route("/categories")
def view_all_categories():

    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    # query to select all categories with limit and offset
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT 
        c.category_id,
        c.category_name
    FROM 
        category c
    LIMIT %s OFFSET %s
    ''', (per_page, offset))
    rows = cur.fetchall()

    # Create a list to hold game data
    categories = []
    if rows:
        for row in rows:
            category_data = {
                "category_id": row[0],
                "category_name": row[1],
            }
            categories.append(category_data)
    else:
        print("not found")

    return render_template("categories/view_categories.html", categories = categories, page = page)

# route to view individual category page
@category_bp.route("/category/<category_id>")
def view_category(category_id):

    # query to select specific developer
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT 
        g.game_id, g.title, c.category_name
    FROM 
        game g
    JOIN 
        game_category gc
    ON 
        g.game_id = gc.game_id
    JOIN 
        category c
    ON 
        c.category_id = gc.category_id
    WHERE 
        gc.category_id = %s;
    ''', (category_id,))
    rows = cur.fetchall()

    games = []
    if rows:
        for row in rows:
            game_data = {
                "game_id": row[0], 
                "game_title": row[1],   
                "category_name": row[2],
            }
            games.append(game_data)
            
    else:
        print("not found")

    return render_template("categories/category.html", games = games)

