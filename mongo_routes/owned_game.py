from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash 
import mysql.connector
import pymongo

# Load configuration
from dotenv import load_dotenv
import os 
load_dotenv('config.env')

import hashlib 
import json 
from datetime import datetime
from auth_utils import login_required # Persistent login 

# MongoDB setup 
import mongo_cfg 

# Integrating everyone part 
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object 
owned_game_bp = Blueprint("owned_game_bp", __name__)

db = None 

def initialize_database(): 
    """Helper function to initialize the MongoDB user collection."""
    global db
    if db is None: 
        # Attempt to get an existing connection
        db = mongo_cfg.get_NoSQLdb()

        # If no existing connection, initialize a new one 
        if db is None: 
            db = mongo_cfg.noSQL_init(app)
        
        return db 

    # After ensuring db is initialised, return the user collection if db is available
    if db is not None: 
        return db 
    else: 
        raise Exception("Failed to initialize MongoDB connection")

# MONGO connections 
@owned_game_bp.route('/test-db-connection')
def mongo_connection(): 
    db = initialize_database()
    if db is None: 
        return "Database not initialized!!", 500
    
    try: 
        # Retrieve all documents 
        documents = db.new_user.find()

        # Iterate through the documents and print them
        all_games = [] 
        for doc in documents: 
            all_games.append({
                "owned_games": doc["owned_games"]
            })

        for doc in documents: 
            print("doc: ", doc)
        
        return f"Successfully connected to MongoDB. all_games: {all_games}", 200
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# Get all owned games by user 
def gamesInOwned(): 
    db = initialize_database()
    if db is None: 
        return "Database is not initalized!!", 500 
  
    try: 
        # Retrieve all documents 
        documents = db.new_user.find({"_id": session["_id"],})

        # Iterate through documents and print them 
        # Fetch all owned_games from user's doc in db
        owned_games_array = []
        for doc in documents:
            owned_games_array.extend(doc["owned_games"])
        
        print("owned game array:", owned_games_array)

        # Fetch additional details about the game
        owned_games_details = []
        for i in owned_games_array:
            owned_games_details.extend(getGameDetails(i["game_id"], i["purchase_date"], i["hours_played"]))

        return owned_games_details
    except Exception as e: 
        return f"Failed to connect to MongoDB: {e}", 500 

# get game details 
def getGameDetails(game_id, purchase_date, hours_played):
    db = initialize_database()
    if db is None: 
        return "Database not initialized", 500

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
                "price_changes" : doc["price_changes"]
                # "price": doc["price"],
                # "categories": doc["categories"],
                # "developers": doc["developers"],
            })
        return game 
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# ---Routes---
# View owned_game
@owned_game_bp.route("/view-owned_game")
@login_required
def view_owned_game():
    # db = initialize_database()
    # if db is None: 
    #     return "Database not initialized!!", 500
    owned_game = gamesInOwned()
    print("owned_game in view: ",owned_game)
    return render_template("owned_game/owned_game.html", owned_game = owned_game)

# add to owned_game
@owned_game_bp.route("/add-owned_game", methods=["POST"])
def add_owned_game():
    db = initialize_database()
    if db is None: 
        return "Database not initialized!!", 500
        
    print(f"Session ID: {session.get('_id')}")
    try: 
        if request.method == "POST":
            game_id = request.form["game"]
            # if not game_id:
            #     return "Game ID is required!", 400
            print("hi")
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            hours = 0


            new_owned_game = { 
                "game_id" : game_id,
                "purchase_date" : date, 
                "hours_played" : hours
            }

            print("hi1")

            db.new_user.update_one(
                {"_id" : session["_id"]},
                {"$push" : {"owned_games" : new_owned_game}}
            )

            print("hi2")

        return view_owned_game()
    except Exception as e: 
        return f"Failed to connect to MongoDB: {e}", 500

# Delete from owned_game
@owned_game_bp.route("/delete-from-owned_game/<game_id>", methods=["GET"])
def delete_owned_game(game_id):
    db = initialize_database()
    if db is None: 
        return "Database not initialized!!", 500
    try: 
        db.new_user.update_one(
            {"_id": session["_id"]},  # Match the document by _id
            {"$pull": {"owned_games": {"game_id": game_id}}}  # Remove the specific game
        )
        return view_owned_game()
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# PRICE HISTORY GRAPH stuff 
# TODO: move into game.py later 

def PriceChanges(_id): 
    db = initialize_database()
    if db is None: 
        return "Database is not initalized!!", 500 
  
    try: 
        # Retrieve all documents 
        documents = db.new_game.find({"_id": _id,})

        # Iterate through documents and print them 
        # Fetch all owned_games from user's doc in db
        game = []
        for doc in documents:
            game.extend(doc["price_changes"])
        
        print("game in PriceChanges():", game)

        # Fetch additional details about the game
        price_changes_details = []
        for i in game:
            price_changes_details.extend(getPriceChangeDetails(_id, i["change_date"], i["base_price"], i["discount"]))
        print("owned_games_details", price_changes_details)

        return price_changes_details
    except Exception as e: 
        return f"Failed to connect to MongoDB: {e}", 500 

# get price change details
def getPriceChangeDetails(_id, change_date, base_price, discount):
    db = initialize_database()
    if db is None: 
        return "Databse not initialized", 500 
    try:
        # Retrieve all documents 
        documents = db.new_game.find({"_id": _id})
        price_changes = []
        for doc in documents: 
            price_changes.append({
                "game_id": doc["_id"],
                "change_date": change_date,
                "base_price": base_price, 
                "discount": discount
            })
        return price_changes
        print("price_changes: ", price_changes)
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# Get all owned games by user 
@owned_game_bp.route('/getPriceChanges/<_id>', methods=["GET"])
def view_price_changes(_id):
        price_changes = PriceChanges(_id)
        print("owned_game in view: ", price_changes)

    # Initialize arrays
        dates_new = []
        prices_new = []

        # Loop through the data
        for change in price_changes:
            # Convert string to datetime
            change_date = datetime.strptime(change['change_date'], '%Y-%m-%d')
            # Format to 'dd-mm-yyyy'
            formatted_date = change_date.strftime('%d-%m-%Y')
            dates_new.append(formatted_date)  # Append to dates array

            # Calculate final price after applying the discount
            final_price = change['base_price'] - (change['base_price'] * (change['discount'] / 100))
            prices_new.append(final_price)  # Append to prices array

        # Output the arrays
        print("Dates:", dates_new)
        print("Prices:", prices_new)
        return render_template("owned_game/graph.html", dates_new = dates_new, prices_new = prices_new)
