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
    # if db is None:
    #     return "Database not initialized!!.", 500
    # try:
    #     collections = db.list_collection_names()
    #     return f"Successfully connected to MongoDB. Collections: {collections}", 200
    # except Exception as e:
    #     return f"Failed to connect to MongoDB: {e}", 500


@review_bp.route("/mongo-test")
def mongo_test():
    db = get_NoSQLdb()

    collection_reviews = db.new_game.find({}, {"reviews": 1, "title": 1})

    # Create a list to hold review data
    all_game_reviews = []
    for doc in collection_reviews:
        for review in doc["reviews"]:
            # Extract review details, assuming review is a dictionary
            review_data = {
                "game_title": doc.get("title", "Unknown Title"),
                "review_date": review.get("review_date", "Unknown Date"),
                "user_id": review.get("user_id", "Unknown User"),
                "recommended": review.get("recommended", False),
                "review_text": review.get("review_text", "No review text provided"),
            }
            all_game_reviews.append(review_data)

    return all_game_reviews