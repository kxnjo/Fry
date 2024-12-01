from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash 
import pymongo

# Load configuration
from dotenv import load_dotenv
import os 
load_dotenv('config.env')

import hashlib 
import json 
from datetime import datetime
import datetime
from auth_utils import login_required # Persistent login 

# MongoDB setup 
from mongo_cfg import get_NoSQLdb

# Create a Blueprint object 
owned_game_bp = Blueprint("owned_game_bp", __name__)

# Get all owned games by user 
def gamesInOwned(user_id=None): 
    db = get_NoSQLdb()
  
    try: 
        if user_id is None:
            user_id = session.get('_id')

        # check if there are any games owned
        document = db.new_user.find_one(
            {"_id": user_id, "owned_games": {"$exists": True, "$ne": []}},  # Check if owned_games is non-empty
            {"owned_games": 1}  # Return only the owned_games field
        )

        if not document:
            return []
        else: 
            owned_games_array = document['owned_games']

            # Fetch additional details about the game
            owned_games_details = []
            for game in owned_games_array:
                owned_games_details.extend(getGameDetails(game["game_id"], game["purchase_date"], game["hours_played"]))

            return owned_games_details
    except Exception as e: 
        return f"ERROR ! {e}", 500 

# get game details 
def getGameDetails(game_id, purchase_date, hours_played):
    db = get_NoSQLdb()

    try: 
        # Retrieve all documents 
        documents = db.new_game.find({"_id": game_id})

        # Iterate through documents and print them 
        game = []
        for doc in documents: 
            game.append({
                "game_id": doc["_id"],
                "title": doc["title"],
                "purchase_date": purchase_date, 
                "hours_played": hours_played,
                "image": doc.get("image", None),
                "price_changes" : doc["price_changes"]
            })
        return game 
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# Used to check if game is purchased as well
def getAddedDates(game_id): # Return added date if game is in wishlist else return None
    db = get_NoSQLdb()

    try:
        document = db.new_user.find_one(
            {"_id": session["_id"], "owned_games.game_id": game_id},
            {"owned_games.$": 1}  # Include only the matched wanted_game
        )
        
        if document and "owned_games" in document:
            return document["owned_games"][0]["added_date"]
        return None
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# ---Routes---
# View owned_game
@owned_game_bp.route("/view-owned_game")
@login_required
def view_owned_game():
    user_id = request.args.get("uid", session['_id'])    # get user id from query params, if not avail, load current logged in user data: session['_id']
    owned_game = gamesInOwned(user_id)

    gamePurchased = getAddedDates("g466860")
    if gamePurchased != None:
        print("Purchased!")
    else:
        print("Not Purchased!")

    return render_template("owned_game/owned_game.html", owned_game = owned_game, current_id = user_id)

# add to owned_game
@owned_game_bp.route("/add-owned_game", methods=["POST"])
def add_owned_game():
    db = get_NoSQLdb()

    try: 
        if request.method == "POST":
            game_id = request.form["game"]
            # if not game_id:
            #     return "Game ID is required!", 400
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            hours = 0

            new_owned_game = { 
                "game_id" : game_id,
                "purchase_date" : date, 
                "hours_played" : hours
            }

            db.new_user.update_one(
                {"_id" : session["_id"]},
                {"$push" : {"owned_games" : new_owned_game}}
            )

        return view_owned_game()
    except Exception as e: 
        return f"Failed to connect to MongoDB: {e}", 500

# Delete from owned_game
@owned_game_bp.route("/delete-from-owned_game/<game_id>", methods=["GET"])
def delete_owned_game(game_id):
    db = get_NoSQLdb()
    try: 
        db.new_user.update_one(
            {"_id": session["_id"]},  # Match the document by _id
            {"$pull": {"owned_games": {"game_id": game_id}}}  # Remove the specific game
        )
        return view_owned_game()
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500