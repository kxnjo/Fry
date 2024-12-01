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
from mongo_cfg import get_NoSQLdb

# integrating everyone's parts # XH TODO: IMPORT OTHER MEMBERS PARTS ONCE UPDATE MONGO!!
from mongo_routes.review import user_written_reviews,mongo_find_review, get_all_reviews_for_game
# from mysql_routes.game import getGameNum, getGames, get_all_games
from mongo_routes.wishlist import getAddedDate
from mongo_routes.owned_game import getAddedDates

# Create a Blueprint object
game_bp = Blueprint("game_bp", __name__)


@game_bp.route('/gametest-db-connection')
def mongo_connection():
    # Ensure db.new_user is initialized
    try:
        db = get_NoSQLdb()

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
    db = get_NoSQLdb()
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
        db = get_NoSQLdb()
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
        user_owned = getAddedDates(game_id)

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
                           gameInWishlist=gameInWishlist,
                           user_owned=user_owned,
                           user_logged_in=bool(user_id),
                           get_user_review=get_user_review,
                           game_reviews=game_reviews, 
                           dates_new = dates_new, 
                           prices_new = prices_new
                           )

@game_bp.route("/edit_game/<game_id>", methods=['POST'])
def edit_game(game_id):

    db = get_NoSQLdb()

    # Get form data
    title = request.form.get("title")
    new_price = request.form.get("price")
    categories = request.form.getlist("categories[]")
    release_date = request.form.get("release_date")
    gameImage = request.files.get("game_image")

    # Validate form data (you can add more checks if needed)
    if not title or not new_price:
        return "Title and price are required!", 400
    
    try:
        new_price = float(new_price)
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

        # If categories are included in the form submission, update them
        if categories:
            update_data["categories"] = categories

        if release_date:
            update_data["release_date"] = release_date

        if gameImage and gameImage.filename != '':
            print("Game image Detected!")
            encoded_img = "data:image/jpeg;base64," + base64.b64encode(gameImage.read()).decode("utf-8")  # Convert image to binary
            update_data["image"] = encoded_img


        # Update the other fields
        db.new_game.update_one({"_id": game_id}, {"$set": update_data})

        return redirect(url_for("user_bp.dashboard"))

    except Exception as e:
        return f"Failed to update the game: {e}", 500
    
@game_bp.route("/create-game/<developer_name>", methods=["POST"])
def create_game(developer_name):
    db = get_NoSQLdb()

    # Get form data
    title = request.form.get("title")
    release_date = request.form.get("release_date")
    price = request.form.get("price")
    categories = request.form.getlist("categories[]")  # Get selected categories as a list
    game_image = request.files.get("game_image")

    # Validate form data
    if not title or not release_date or not price or not categories:
        flash("All fields are required!", "danger")
        return redirect(url_for("game_bp.create_game", developer_name=developer_name))  # Or return to the add game modal

    try:

        # Create the new game document with the required structure
        new_game = {
            "_id": f"g{int(datetime.utcnow().timestamp())}",  # Generate a unique _id based on timestamp (you can change this logic)
            "title": title,
            "release_date": release_date,
            "price": float(price),  # Ensure the price is saved as a float
            "price_changes": [{
                "change_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "base_price": float(price),
                "discount": 0  # You can handle discounts later if needed
            }],
            "reviews": [],  # Initial empty reviews array
            "categories": categories,  # Save the selected categories
            "developers": [developer_name],  # Save the developer_name as a list with one item
        }

        if game_image and game_image.filename != '':
            encoded_img = "data:image/jpeg;base64," + base64.b64encode(game_image.read()).decode("utf-8")  # Convert image to binary and then base64
            new_game["image"] = encoded_img


        # Insert the new game into the database
        db.new_game.insert_one(new_game)

        flash("Game created successfully!", "success")
        return redirect(url_for("user_bp.dashboard"))  # Redirect to the dashboard or wherever appropriate

    except Exception as e:
        flash(f"Failed to create the game: {e}", "danger")
        return redirect(url_for("game_bp.create_game", developer_name=developer_name))


@game_bp.route("/delete-game/<game_id>", methods=["POST"])
def delete_game(game_id):
    db = get_NoSQLdb()  # Connect to the database

    try:
        # Attempt to delete the game from the database
        result = db.new_game.delete_one({"_id": game_id})
        
        if result.deleted_count == 0:
            return "Game not found or already deleted", 404

        # Redirect back to the dashboard after deletion
        return redirect(url_for("user_bp.dashboard"))

    except Exception as e:
        return f"Error occurred while deleting the game: {e}", 500

def PriceChanges(_id): 
    db = get_NoSQLdb()
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
    db = get_NoSQLdb()
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



