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

# Create a Blueprint object
developer_bp = Blueprint("developer_bp", __name__)

# route to view all developers page
@developer_bp.route("/developers")
def view_all_developers():

    page = request.args.get('page', 1, type=int)

    # Define the limit of items per page
    per_page = 20

    # Calculate the offset for the query
    offset = (page - 1) * per_page

    db = get_NoSQLdb()

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

    return render_template("developers/view_developers.html", 
                            developers=developers_paginated,
                            page=page,
                            total_pages=total_pages)

# route to view individual developer page
@developer_bp.route("/developer/<developer>")
def view_developer(developer):

    # Connect to the database
    db = get_NoSQLdb()

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
    
    return render_template("developers/developer.html", 
                            games=game_data, 
                            developer=developer, 
                            page=page, 
                            total_pages=total_pages)

