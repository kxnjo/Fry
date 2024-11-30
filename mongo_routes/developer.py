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
import mongo_cfg

# integrating everyone's parts # XH TODO: IMPORT OTHER MEMBERS PARTS ONCE UPDATE MONGO!!
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
# from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object
developer_bp = Blueprint("developer_bp", __name__)

db = None

# MARK: initialise database
def get_db():
    """Helper function to initialize the MongoDB user collection."""
    global db
    if db is None:
        # Attempt to get an existing connection first
        db = mongo_cfg.get_NoSQLdb()
        
        # If no existing connection, initialize a new one
        if db is None:
            db = mongo_cfg.noSQL_init(app)
        
        return db
            
    # After ensuring db is initialized, return the user collection if db is available
    if db is not None:
        return db
    else:
        raise Exception("Failed to initialize MongoDB connection")

db = get_db()

# route to view all developers page
@developer_bp.route("/developers")
def view_all_developers():

    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    db = get_db()  # Assuming you're using MongoDB and `get_db()` retrieves the db connection

    try:
        # Find all unique developers from the "developers" field in all game documents
        all_developers = db.new_game.distinct("developers")

        # Paginate developers
        developers_paginated = all_developers[offset: offset + per_page]

        # Calculate total pages
        total_developers = len(all_developers)
        total_pages = (total_developers + per_page - 1) // per_page

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

    return render_template("developers/view_developers.html", developers=developers_paginated,
        page=page,
        total_pages=total_pages)

# route to view individual developer page
@developer_bp.route("/developer/<developer>")
def view_developer(developer):

    # Connect to the database
    db = get_db()

    # Get the current page number from the request (default to 1 if not provided)
    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 20

    # Calculate the offset for the query
    offset = (page - 1) * per_page

    try:
        # Find all games that contain the selected developer (with pagination)
        games_cursor = db.new_game.find({"developers": developer}).skip(offset).limit(per_page)

        # Prepare the list of games
        game_data = []
        for game in games_cursor:
            game_data.append({
                "game_id": game["_id"],
                "game_title": game["title"],
                "developers": game["developers"]
            })

        # Get the total number of games in the developer for pagination (to calculate the number of pages)
        total_games = db.new_game.count_documents({"developers": developer})
        total_pages = (total_games // per_page) + (1 if total_games % per_page > 0 else 0)

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    
    return render_template("developers/developer.html", games=game_data, developer=developer, page=page, total_pages=total_pages)
