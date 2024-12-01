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
from datetime import datetime
from auth_utils import login_required  # persistent login

# MongoDB setup
import mongo_cfg

# integrating everyone's parts # XH TODO: IMPORT OTHER MEMBERS PARTS ONCE UPDATE MONGO!!
from mysql_routes.review import user_written_reviews,mongo_find_review,mongo_find_owned, get_all_reviews_for_game
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
# from mysql_routes.game import getGameNum, getGames, get_all_games
from mongo_routes.wishlist import getAddedDate
from mongo_routes.owned_game import getAddedDates

# Create a Blueprint object
game_bp = Blueprint("game_bp", __name__)

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

@game_bp.route('/gametest-db-connection')
def mongo_connection():
    # Ensure db.new_user is initialized
    try:
        db = get_db()

        # Retrieve all documents
        documents = db.new_game.find()

        # Iterate through documents and print them
        all_games = []
        for game in documents:            
            # print(f"this is indiv game! {game}")
            all_games.append(game)

        return f"Successfully connected to MongoDB. all_games: {all_games}", 200
    
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    

# route to view games page
@game_bp.route("/games", methods=['GET'])
def view_all_games():
    db = get_db()
    search = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'title')  # Default sort is by title
    sort_order = request.args.get('order', 'asc')  # Default order is ascending

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    sort_direction = 1 if sort_order == 'asc' else -1

    if db is None:
        return "Database not initialized!!", 500

    try:
        # Build the search filter
        search_filter = {}
        if search:
            search_filter = {"title": {"$regex": search, "$options": "i"}}  # Case-insensitive search

        # Determine sort field
        sort_field = "title"  # Default sort field
        if sort_by == "price":
            sort_field = "price"
        elif sort_by == "release_date":
            sort_field = "release_date"

        # Query the database with search, sort, skip, and limit
        documents = (
            db.new_game.find(search_filter)
            .sort(sort_field, sort_direction)
            .skip(offset)
            .limit(per_page)
        )

        # Count the total documents matching the filter
        total_documents = db.new_game.count_documents(search_filter)


        # Iterate through documents and print them
        all_games = []
        for doc in documents:
            all_games.append({
                "_id": doc["_id"],
                "title": doc["title"],
                "release_date": doc["release_date"],
                "price": float(doc["price"]),
                "image": doc.get("image"),
                "categories": doc["categories"]
            })

        # Calculate total pages
        total_pages = (total_documents + per_page - 1) // per_page

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500
    
    return render_template("games/view_games.html", games=all_games, page=page, sort_by=sort_by,
                           sort_order=sort_order, search=search, total_pages = total_pages)


# route to view individual game page
@game_bp.route("/game/<game_id>")
def view_game(game_id):
    try:
        db = get_db()
        doc = db.new_game.find_one({"_id":  game_id,})
        game = {
            "game_id": doc["_id"],
            "game_title": doc["title"],
            "game_release_date": doc["release_date"],
            "game_price": doc["price"],
            "image": doc.get("image"),
            "categories": doc.get("categories", []),
            "developers": doc.get("developers", [])
        }
        user_id = session.get('_id')

        user_owned = mongo_find_owned(user_id, game_id)

        # Find the review
        find_user_review = mongo_find_review(user_id, game_id)
        get_user_review = None

        if find_user_review:  # If there's a review found
            user_review = find_user_review["reviews"][0]  # Get the review object
            get_user_review = {
                "review_date": user_review.get("review_date", "NA"),  # Review date or "NA" if not available
                "review_text": user_review.get("review_text", "No review text"),  # Review text
                "recommended": user_review.get("recommended", "NA")  # Recommended value or "NA" if not available
            }
        game_reviews = get_all_reviews_for_game(game_id)
        gameInWishlist = getAddedDate(game_id)
        gamePurchased = getAddedDates(game_id)

        price_changes = PriceChanges(game_id)
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

    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

    return render_template("games/game.html",
                           game=game,
                        #    reviews=reviews,
                        #    recommended_data=recommended_data,
                           gameInWishlist=gameInWishlist,
                           gamePurchased=gamePurchased,
                           user_logged_in=bool(user_id),
                           user_owned=bool(user_owned),
                           get_user_review=get_user_review,
                           game_reviews=game_reviews, 
                           dates_new = dates_new, 
                           prices_new = prices_new
                        #    dates=dates,
                        #    prices=prices
                           )

@game_bp.route("/edit_game/<game_id>", methods=['POST'])
def edit_game(game_id):

    db = get_db()

    # Get form data
    title = request.form.get("title")
    new_price = request.form.get("price")

    # Validate form data (you can add more checks if needed)
    if not title or not new_price:
        return "Title and price are required!", 400
    
    try:
        # Retrieve the current game document
        game = db.new_game.find_one({"_id": game_id})
        if not game:
            return "Game not found!", 404

        # Get the current price to compare with the new price
        current_price = game.get("price")

        # Update the game document
        update_data = {"title": title}
        if current_price != new_price:  # Only add price change if the price is updated
            update_data["price"] = new_price

            # Create a new price change record
            new_price_change = {
                "change_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "base_price": float(new_price),
                "discount": game.get("price_changes", [{}])[-1].get("discount", 0),  # Preserve the last discount
            }

            # Append the new price change to the `price_changes` array
            db.new_game.update_one(
                {"_id": game_id},
                {"$push": {"price_changes": new_price_change}}
            )

        # Update the other fields
        db.new_game.update_one({"_id": game_id}, {"$set": update_data})

        return redirect(url_for("user_bp.dashboard"))

    except Exception as e:
        return f"Failed to update the game: {e}", 500
    
@game_bp.route("/create-game", methods=["POST"])
def create_game(game_id):
    # something (placeholder)

    return redirect(url_for("user_bp.dashboard"))

@game_bp.route("/delete-game/<game_id>", methods=["POST"])
def delete_game(game_id):
    # something (placeholder)

    return redirect(url_for("user_bp.dashboard"))

def PriceChanges(_id): 
    db = get_db()
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
    db = get_db()
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



