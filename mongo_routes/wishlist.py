from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash
import mysql.connector
import pymongo

# images import
from bson.binary import Binary
import base64

# load up configurations
from dotenv import load_dotenv
import os
load_dotenv('config.env')

import hashlib
import json
import datetime
from auth_utils import login_required  # persistent login

# MongoDB setup
import mongo_cfg

# integrating everyone's parts
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object
wishlist_bp = Blueprint("wishlist_bp", __name__)

db = None

# Functions
def initialize_database():
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

# Get all games in wishlist by user
def gamesInWishlist():
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        # Retrieve all documents
        documents = db.new_user.find({"_id":  session["_id"],})

        # Iterate through documents and print them
        wanted_games = []
        for doc in documents:
            # Extend the wishlist with the wanted_games list
            wanted_games.extend(doc["wanted_games"])
        
        wishlist_game = []
        for i in wanted_games:
            wishlist_game.extend(getGame(i["added_date"], i["game_id"]))
        
        return wishlist_game
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# Get game details
def getGame(added_date, game_id):
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        # Retrieve all documents
        documents = db.new_game.find({"_id":  game_id,})

        # Iterate through documents and print them
        game = []
        for doc in documents:
            game.append({
                "game_id": doc["_id"],
                "title": doc["title"],
                "price": doc["price"],
                "categories": doc["categories"],
                "developers": doc["developers"],
                "added_date" : added_date
            })
        return game
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# Used to check if game is in wishlist as well
def getAddedDate(game_id): # Return added date if game is in wishlist else return None
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        document = db.new_user.find_one(
            {"_id": session["_id"], "wanted_games.game_id": game_id},
            {"wanted_games.$": 1}  # Include only the matched wanted_game
        )
        
        if document and "wanted_games" in document:
            return document["wanted_games"][0]["added_date"]
        return None
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    
# Recommend game by game category
def recommendGame(game_id):
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        gameDocument = db.new_game.find({"_id":  game_id,})
        categories = []
        for doc in gameDocument:    
            categories.extend(doc["categories"])
            
        # Query to fetch recommended games
        pipeline = [
            # Match games with at least one category in the target game's categories
            {"$match": {"categories": {"$in": categories}}},
            
            # Exclude the original game itself
            {"$match": {"_id": {"$ne": game_id}}},

            # Randomize the results
            {"$sample": {"size": 3}}
        ]

        # Run the aggregation pipeline
        recommendGameDoc = list(db.new_game.aggregate(pipeline))

        # Extract just the game_ids
        recommendGame = [game["_id"] for game in recommendGameDoc]
        
        return recommendGame
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    

# Routes
@wishlist_bp.route('/view-wishlist')
def viewWishlist():
    wishlist_game = gamesInWishlist()
    
    seen_game_ids = set()
    unique_games = []
    recommendations = []
    
    for i in wishlist_game:
        recommendations.extend(recommendGame(i["game_id"]))
    
    # Remove duplicates
    for game_id in recommendations:
        if game_id not in seen_game_ids:
            unique_games.append(game_id)
            seen_game_ids.add(game_id)

    gameRecommendation = []
    count = 0
    for game_id in unique_games:
        gameRecommendation.extend(getGame("-", game_id))
        count += 1
        if (count >= 3): break
    
    gameInWishlist = getAddedDate("g10")
    if gameInWishlist != None:
        print("Found in wishlist!")
    else:
        print("Not in wishlist!")

    return render_template("wishlist/wishlist.html", wishlist_game=wishlist_game, search=False, gameRecommendation=gameRecommendation)

@wishlist_bp.route("/add-to-wishlist", methods=["POST"])
def addToWishlist():
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        if request.method == "POST":
            game_id = request.form["game_id"]
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            
            new_game_wishlist = {
                "game_id": game_id,
                "added_date": date
            }
            
            db.new_user.update_one(
                {"_id": session["_id"]},  
                {"$push": {"wanted_games": new_game_wishlist}}
            )
            
        return viewWishlist()
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

@wishlist_bp.route("/delete-from-wishlist/<game_id>", methods=["GET"])
def deleteFromWishlist(game_id):
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        db.new_user.update_one(
            {"_id": session["_id"]},  # Match the document by _id
            {"$pull": {"wanted_games": {"game_id": game_id}}}  # Remove the specific game
        )
        return viewWishlist()
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    
@wishlist_bp.route("/search-wishlist", methods=["POST"])
def searchWishlist():
    if request.method == "POST":
        wishlist_games = gamesInWishlist()
        wishlist_game_ids = [game["game_id"] for game in wishlist_games]
        
        string = request.form["searchInput"]  # Get search input and convert to lowercase

        # MongoDB query with case-insensitive search in title, categories, and developers
        search_result = db.new_game.find(
        {
            "$and": [
                {"_id": {"$in": wishlist_game_ids}},  # Ensure game_id is in the wishlist
                {
                    "$or": [
                        {"title": {"$regex": string.lower(), "$options": "i"}},         # Match in title
                        {"categories": {"$regex": string.lower(), "$options": "i"}},    # Match in categories
                        {"developers": {"$regex": string.lower(), "$options": "i"}}     # Match in developers
                    ]
                }
            ]
        },
        {"_id": 1}  # Get only the game_id 
    )
        
        # Extract the game_id values into a list
        game_ids = [game["_id"] for game in search_result]
        searchResult = []
        for i in game_ids:
            added_date = getAddedDate(i)
            searchResult.extend(getGame(added_date, i))
        
        return render_template("wishlist/wishlist.html", search=True, searchResult=searchResult, string=string)
    return

