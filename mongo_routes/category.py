from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash
import pymongo

# images import
from bson.binary import Binary
import base64
import bcrypt

# load up configurations
from dotenv import load_dotenv
import os
load_dotenv('config.env')

import json
from datetime import date
from auth_utils import login_required  # persistent login

# MongoDB setup
from mongo_cfg import get_NoSQLdb

# integrating everyone's parts # XH TODO: IMPORT OTHER MEMBERS PARTS ONCE UPDATE MONGO!!
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
# from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object
category_bp = Blueprint("category_bp", __name__)

# route to view all categories
@category_bp.route("/categories")
def view_all_categories():

    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    db = get_NoSQLdb()  # Assuming you're using MongoDB and `get_db()` retrieves the db connection

    try:
        # Find all unique categories from the "categories" field in all game documents
        all_categories = db.new_game.distinct("categories")

        # Paginate categories
        categories_paginated = all_categories[offset: offset + per_page]

        # Calculate total pages
        total_categories = len(all_categories)
        total_pages = (total_categories + per_page - 1) // per_page

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

    return render_template(
        "categories/view_categories.html",
        categories=categories_paginated,
        page=page,
        total_pages=total_pages
    )

# route to view individual category page with pagination
@category_bp.route("/category/<category>")
def view_category(category):

    # Connect to the database
    db = get_NoSQLdb()

    # Get the current page number from the request (default to 1 if not provided)
    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 20

    # Calculate the offset for the query
    offset = (page - 1) * per_page

    try:
        # Find all games that contain the selected category (with pagination)
        games_cursor = db.new_game.find({"categories": category}).skip(offset).limit(per_page)

        # Prepare the list of games
        game_data = []
        for game in games_cursor:
            game_data.append({
                "game_id": game["_id"],
                "game_title": game["title"],
                "categories": game["categories"]
            })

        # Get the total number of games in the category for pagination (to calculate the number of pages)
        total_games = db.new_game.count_documents({"categories": category})
        total_pages = (total_games // per_page) + (1 if total_games % per_page > 0 else 0)

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

    # Return the category page template with the filtered games and pagination info
    return render_template("categories/category.html", games=game_data, category=category, page=page, total_pages=total_pages)