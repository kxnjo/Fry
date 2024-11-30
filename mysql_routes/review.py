from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector

from dotenv import load_dotenv
import os

load_dotenv('config.env')
from auth_utils import login_required  # persistent login
import random, datetime

# mongo
from mongo_cfg import get_NoSQLdb
# Create a Blueprint object
review_bp = Blueprint("review_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_DATABASE"),
    )

@review_bp.route('/test-db-connection')
def mongo_connection():
    #
    # db = get_NoSQLdb()
    # get_reviews = db.new_game.find({"reviews": 1})
    #
    # print(get_reviews)
    db = get_NoSQLdb()

    # Correct way to query MongoDB for specific fields
    # Use projection to get only the "reviews" field
    get_reviews = db.new_game.find({}, {"reviews": 1})

    # Convert the MongoDB cursor to a list and print the result
    reviews_list = list(get_reviews)  # Convert cursor to list to retrieve all documents
    print(reviews_list)  # This will print the reviews in the terminal/log

    return {"reviews": reviews_list}  # Return the reviews in the response (JSON)

@review_bp.route("/mongo-test", methods=["GET"])
def mongo_test():
    selected_game = request.args.get("game")  # returns game_id from selected dropdown
    recommended = request.args.get("recommended")

    # Print for debugging
    print("Selected value: " + (selected_game if selected_game is not None else "None"))
    print("Recommended value: " + (recommended if recommended is not None else "None"))

    filter_query = {}
    if selected_game:
        filter_query["_id"] = selected_game
    if recommended:
        filter_query["reviews.recommended"] = True

    db = get_NoSQLdb()
    user_id = session.get('_id')

    page = request.args.get("page", 1, type=int)  # get current page number, default to first page
    items_per_page = 10  # set the number of items per page

    reviews = []  # This will store the review data
    games = []  # This will store the game metadata

    # Fetch all games to populate the dropdown
    all_games = db.new_game.find({}, {"_id": 1, "title": 1})  # Query for all games

    # Fetch the games that match the filter criteria
    game_reviews_cursor = db.new_game.find(filter_query, {"reviews": 1, "title": 1, "_id": 1})

    # Create a list to hold all reviews (flattened reviews across games)
    all_reviews = []

    for doc in game_reviews_cursor:
        game_data = {
            "id": doc["_id"],
            "title": doc["title"]
        }
        games.append(game_data)  # Adding game metadata to games list

        # Flatten all reviews for the game and filter by 'recommended' if needed
        for review in doc["reviews"]:
            if not recommended or review.get("recommended", False):  # Apply 'recommended' filter
                review_data = {
                    "game_title": doc["title"],
                    "review_date": review["review_date"],
                    "user_id": review["user_id"],
                    "recommended": review["recommended"],
                    "review_text": review["review_text"]
                }
                all_reviews.append(review_data)

    # Calculate total number of reviews
    total_reviews = len(all_reviews)

    # Calculate total pages for pagination
    total_pages = (total_reviews + items_per_page - 1) // items_per_page

    # Apply pagination: skip the correct number of reviews and limit to the number of items per page
    reviews = all_reviews[(page - 1) * items_per_page : page * items_per_page]

    return render_template(
        "reviews/review-mongo.html",
        reviews=reviews,
        games=games,
        selected_game=selected_game,
        recommended=recommended,
        page=page,
        total_pages=total_pages
    )

@review_bp.route('/review-add', methods=['POST'])
# @review_bp.route('review-add/<review_id>', methods=['POST'])
def mongo_add():
    db = get_NoSQLdb()
    user_id = session.get('_id')

    # Retrieve selected game and review data from the POST request
    selected_game = request.form['game_id']  # This will contain the game ID
    recommended = request.form['recommended']  # contain the recommended value
    review_text = request.form['review_text']  # contain the review_text content
    print("mongo_add g_id : " + selected_game)
    print("mongo recommended: " + recommended)
    print("mongo review_Text: " + review_text)

    source = request.form['source']
    # Determine the recommended value
    recommended_val = True if recommended == "Recommended" else False


    review_check = mongo_find_review(user_id,selected_game)
    if review_check:
        # The review exists, so we will update it
        update_review = {
            '$set': {
                'reviews.$.review_text': review_text,  # Update the review_text of the matched review
                'reviews.$.recommended': recommended_val  # Update the recommended value
            }
        }

        # Update the review in the database
        db.new_game.update_one(
            {'_id': selected_game, 'reviews.user_id': user_id},  # Find the game and review by user_id
            update_review  # Apply the update
        )
        print("updated one")
    else: # ITS NEW
        print("nope new")
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        print(date)
        new_review = {
            'review_text': review_text,
            'review_date': date,
            'user_id': user_id,
            'recommended': recommended_val
        }

        # Insert the new review into the 'reviews' array
        db.new_game.update_one(
            {'_id': selected_game},  # Find the game by game_id
            {'$push': {'reviews': new_review}}  # Append the new review to the reviews array
        )

    # Redirect based on the source
    if source == 'dashboard':
        return redirect(url_for('user_bp.dashboard'))
    else:
        return redirect(url_for('game_bp.view_game', game_id=selected_game))


def mongo_find_owned(user_id, game_id):
    db = get_NoSQLdb()
    result = db.new_user.find(
        {
            "_id": user_id,
            "reviews": {"$elemMatch": {"game_id": game_id}}  # Match the user_id inside reviews
        }
    )
    if result:
        return True
    else:
        return False

def mongo_find_review(user_id, game_id):
    # Get the database
    db = get_NoSQLdb()

    # Find the game by game_id and user_id
    result = db.new_game.find(
        {
            "_id": game_id,  # Match the game_id to the _id field
            "reviews": {"$elemMatch": {"user_id": user_id}}  # Match the user_id inside reviews
        },
        {"title": 1, "reviews.$": 1}  # Projection to return only title and matched review
    )
    # Convert the result to a list and check if there are any reviews
    result_list = list(result)  # Convert the cursor to a list
    if result_list:
        print("this is list[0]")
        print(result_list[0])
        return result_list[0]  # Return the first (and possibly only) document with reviews
    else:
        return None  # No review found for this user and game

# @review_bp.route('/review-edit/<game_id>/<review_id>', methods=['GET', 'POST'])
@review_bp.route('/mongo-edit/<game_id>/', methods=['GET', 'POST'])
def edit_reviews(game_id):

    db = get_NoSQLdb()
    selected_game = game_id
    user_id = session.get('_id')  # Get user_id from the session
    review_info = None  # Initialize to None
    game_title = db.new_game.find_one(
        {
            "_id": game_id,  # Match the game_id to the _id field
        },
        {"title": 1}  # Projection to return only title and matched review
    )
    if game_title:
        title = game_title['title']
    # Get the title from the document and print it
    find_user_review = mongo_find_review(user_id, game_id)

    # Print the structure of find_user_review to debug
    print("find_user_review:", find_user_review)

    if find_user_review:  # If there's a review found
        user_reviews = find_user_review.get("reviews", [])  # Get all reviews (not just the first one)

        if user_reviews:
            print("User reviews found:", user_reviews)  # Debugging print for review details

            # Iterate through all reviews
            review_info = []
            for user_review in user_reviews:
                review_info.append({
                    "review_date": user_review.get("review_date", "NA"),  # Review date or "NA" if not available
                    "review_text": user_review.get("review_text", "No review text"),  # Review text
                    "recommended": user_review.get("recommended", "NA")  # Recommended value or "NA" if not available
                })
        else:
            print("No reviews found for this user.")
    else:
        print("No user review found for this game.")

    print(review_info)

    return render_template(
        "reviews/review-edit-mongo.html",
        selected_game=selected_game,
        game_title=title,
        review_info=review_info,  # This will contain all the reviews
    )

def user_written_reviews(user_id):
    # Start connection
    db = get_NoSQLdb()
    # Find the game by game_id and user_id
    user_reviews = db.new_game.find(
        {
            "reviews": {"$elemMatch": {"user_id": user_id}}  # Match the user_id inside reviews
        },
        {"game_id": 1, "title": 1, "reviews.$": 1}  # Projection to return only title and matched review
    )

    # Convert cursor to list and print to inspect the results
    reviews = []

    # Convert the cursor to a list and check if we found any reviews
    user_reviews_list = list(user_reviews)
    if user_reviews_list:
        for game in user_reviews_list:
            for user_review in game['reviews']:
                if user_review["user_id"] == user_id:  # Confirm it's the review for the correct user
                    review_data = {
                        "game_id": game["_id"],
                        "game_title": game["title"],
                        "review_date": user_review["review_date"],
                        "user_id": user_review["user_id"],
                        "recommended": user_review["recommended"],
                        "review_text": user_review["review_text"]
                    }
                    reviews.append(review_data)
    else:
        print(f"No reviews found for user_id: {user_id}")

    return reviews  # Return the list of reviews for the user

# Delete Review
# @review_bp.route("review-delete/<review_id>", methods=['GET'])
@review_bp.route("review-delete/", methods=['GET'])
def delete_review():
    db = get_NoSQLdb()
    user_id = session.get('_id')
    # Retrieve game_id and source from URL query parameters
    game_id = request.args.get('game_id')
    source = request.args.get('source')
    print(game_id)
    print(source)
    db.new_game.update_one(
        {'_id': game_id},  # Match the game document by ID
        {'$pull': {'reviews': {'user_id': user_id}}}  # Remove the review with the matching user_id
    )

    # Redirect based on the source
    if source == 'dashboard':
        return redirect(url_for('user_bp.dashboard'))
    else:
        return redirect(url_for('game_bp.view_game', game_id=game_id))


def get_all_reviews_for_game(game_id):
    # Get the database
    db = get_NoSQLdb()

    # Find the game by game_id
    result = db.new_game.find_one(
        {"_id": game_id},  # Match the game_id to the _id field
        {"title": 1, "reviews": 1}  # Projection to return only title and reviews
    )

    if result and "reviews" in result:
        # Split the reviews into two lists based on the `recommended` field
        recommended_reviews = [review for review in result["reviews"] if review.get("recommended") is True]
        not_recommended_reviews = [review for review in result["reviews"] if review.get("recommended") is False]

        # Collect all user_ids from reviews
        all_user_ids = {review["user_id"] for review in result["reviews"]}

        # Fetch usernames from the users collection
        users = db.new_user.find({"_id": {"$in": list(all_user_ids)}}, {"username": 1})
        user_map = {user["_id"]: user["username"] for user in users}

        # Add the username to each review
        for review in recommended_reviews:
            review["username"] = user_map.get(review["user_id"], "Unknown User")

        for review in not_recommended_reviews:
            review["username"] = user_map.get(review["user_id"], "Unknown User")

        print(recommended_reviews)
        # Print for debugging purposes
        print(f"Game Title: {result['title']}")
        print(f"Recommended Reviews: {len(recommended_reviews)}")
        print(f"Not Recommended Reviews: {len(not_recommended_reviews)}")

        return {
            "title": result["title"],
            "recommended_reviews": recommended_reviews,
            "not_recommended_reviews": not_recommended_reviews
        }
    else:
        return None  # No reviews found or game doesn't exist
