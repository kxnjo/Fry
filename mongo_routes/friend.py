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

# Create a Blueprint object
friendlist_bp = Blueprint("friendlist_bp", __name__)

db = None

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
    
@friendlist_bp.route("/view-friends")
@login_required
def view_friends():
    try:
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500
        
        user_id = session["_id"]  # Get the user_id from the session

        # Retrieve the user's data
        user = db.new_user.find_one({'_id': user_id})
        if not user:
            return "User not found", 404

        # Safely get friends, defaulting to empty list if None
        user_friends = user.get('friends', [])
        
        # Get friend IDs, handling potential None values
        friend_ids = [friend.get('friend_id') for friend in user_friends if friend and friend.get('friend_id')]
        
        # Retrieve friends' data
        friends = list(db.new_user.find({"_id": {"$in": friend_ids}}))

        # Prepare friend data
        friend_data = []
        
        for friend in friends:
            # Safely get friends for this friend
            friend_friends = friend.get('friends', [])
            
            # Find mutual friends
            mutual_friend_ids = [
                f.get('friend_id') for f in user_friends 
                if f and f.get('friend_id') in [f2.get('friend_id') for f2 in friend_friends]
            ]
            
            # Retrieve mutual friends details
            mutual_friends = list(db.new_user.find({
                '_id': {'$in': mutual_friend_ids}
            }))

            # Safely get game titles
            owned_game_titles = [
                db.new_game.find_one({'_id': game['game_id']})['title'] 
                for game in friend.get('owned_games', []) 
                if db.new_game.find_one({'_id': game['game_id']})
            ]

            wanted_game_titles = [
                db.new_game.find_one({'_id': game['game_id']})['title'] 
                for game in friend.get('wanted_games', []) 
                if db.new_game.find_one({'_id': game['game_id']})
            ]

            friend_data.append({
                'friend_id': friend['_id'],
                'friendship_date': friend.get('created_on', 'Unknown'),
                'username': friend.get('username', 'Unknown'),
                'wanted_games': wanted_game_titles,
                'owned_games': owned_game_titles,
                'mutual_friends': [{
                    'user_id': mf['_id'],
                    'username': mf['username']
                } for mf in mutual_friends]
            })

    except Exception as e:
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"

    return render_template("friend/friend.html", friend_data=friend_data)

@friendlist_bp.route("/add-friend", methods=["GET", "POST"])
# Function to add a friend
def add_friend():
    try:
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500
        
        if request.method == "POST":
            user_id = session["_id"]  # Get the user_id from the session
            friend_username = request.form["friend_username"]

            # Retrieve the user's data
            user = db.new_user.find_one({'_id': user_id})

            # Check if the friend exists
            friend = db.new_user.find_one({'username': friend_username})

            if friend is None:
                flash("User not found")
                return redirect(url_for("friendlist_bp.add_friend"))

            # Check if the user is already friends with the friend
            if friend['_id'] in [friend['friend_id'] for friend in user['friends']]:
                flash("You are already friends with this user")
                return redirect(url_for("friendlist_bp.add_friend"))

            # Add the friend to the user's friend list
            db.new_user.update_one(
                {'_id': user_id},
                {'$push': {'friends': {
                    'friend_id': friend['_id'],
                    'created_on': datetime.datetime.now()
                }}}
            )

            # Add the user to the friend's friend list
            db.new_user.update_one(
                {'_id': friend['_id']},
                {'$push': {'friends': {
                    'friend_id': user_id,
                    'created_on': datetime.datetime.now()
                }}}
            )

            flash("Friend added successfully")
            return redirect(url_for("friendlist_bp.add_friend"))

    except Exception as e:
        print(f"Error: {e}")
        return f"Error adding friend: {e}"

    return render_template("friend/add_friend.html")

@friendlist_bp.route("/delete-friend/<friend_id>")
# Function to delete a friend
def delete_friend(friend_id):
    try:
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500
        
        user_id = session["_id"]  # Get the user_id from the session

        # Retrieve the user's data
        user = db.new_user.find_one({'_id': user_id})

        # Check if the friend exists
        friend = db.new_user.find_one({'_id': friend_id})

        if friend is None:
            flash("Friend not found")
            return redirect(url_for("friendlist_bp.view_friends"))

        # Remove the friend from the user's friend list
        db.new_user.update_one(
            {'_id': user_id},
            {'$pull': {'friends': {'friend_id': friend_id}}}
        )

        # Remove the user from the friend's friend list
        db.new_user.update_one(
            {'_id': friend_id},
            {'$pull': {'friends': {'friend_id': user_id}}}
        )

        flash("Friend deleted successfully")
        return redirect(url_for("friendlist_bp.view_friends"))

    except Exception as e:
        print(f"Error: {e}")
        return f"Error deleting friend: {e}"