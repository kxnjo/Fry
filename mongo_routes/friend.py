from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash, get_flashed_messages
import pymongo

# images import
from bson.binary import Binary

# load up configurations
from dotenv import load_dotenv
import os
load_dotenv('config.env')

import datetime
import traceback
import random
from auth_utils import login_required  # persistent login

# MongoDB setup
from mongo_cfg import get_NoSQLdb

# Create a Blueprint object
friendlist_bp = Blueprint("friendlist_bp", __name__)


# MARK: FUNCTIONS USED BY OTHER FILES
def get_user_friends(user_id=None):
    db = get_NoSQLdb()

    if user_id == None:
        user_id = session['_id']

    # Retrieve the user document
    user = db.new_user.find_one({'_id': user_id}, {'friends': 1})  # Only fetch the 'friends' field
    if not user:
        return f"User with ID {user_id} not found!", 404

    # Extract the list of friend IDs
    friend_ids = [friend['friend_id'] for friend in user.get('friends', [])]
    
    # Fetch friend details
    friends = list(db.new_user.find({'_id': {'$in': friend_ids}}, {'_id': 1, 'username': 1}))
    
    return friends


def get_mutual_friends(user_id_1, user_id_2):
    db = get_NoSQLdb()

    # Fetch friends for both users
    user1 = db.new_user.find_one({'_id': user_id_1}, {'friends': 1})
    user2 = db.new_user.find_one({'_id': user_id_2}, {'friends': 1})

    if not user1 or not user2:
        return "One or both users not found!", 404

    # Get friend IDs for both users
    user1_friend_ids = {friend['friend_id'] for friend in user1.get('friends', [])}
    user2_friend_ids = {friend['friend_id'] for friend in user2.get('friends', [])}

    # Find mutual friend IDs (intersection of sets)
    mutual_friend_ids = user1_friend_ids & user2_friend_ids

    # Fetch details of mutual friends
    mutual_friends = list(db.new_user.find({'_id': {'$in': list(mutual_friend_ids)}}, {'_id': 1, 'username': 1}))

    return mutual_friends
    

# MARK: ROUTE FUNCTIONS
@friendlist_bp.route("/view-friends")
@login_required
def view_friends():
    try:
        db = get_NoSQLdb()
        
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
def add_friend():
    try:
        db = get_NoSQLdb()
        
        # Get user_id from session
        user_id = session.get("_id")
        if not user_id:
            return redirect(url_for("login"))

        # Retrieve the user's data
        user = db.new_user.find_one({'_id': user_id})
        if not user:
            return redirect(url_for("login"))

        # Get existing friend IDs
        existing_friend_ids = [friend.get('friend_id') for friend in user.get('friends', [])]
        
        # Find suggested friends (users not in friend list)
        all_suggested_friends = list(db.new_user.find({
            '_id': {
                '$ne': user_id,  
                '$nin': existing_friend_ids  
            }
        }))

        # Randomly pick 4 suggestions
        suggested_friends = random.sample(all_suggested_friends, min(len(all_suggested_friends), 4))

        if request.method == "POST":
            friend_username = request.form.get("friend")
            if not friend_username:
                return redirect(url_for("friendlist_bp.add_friend"))

            # Check if the friend exists
            friend = db.new_user.find_one({'username': friend_username})
            if friend is None:
                flash("User not found")
                get_flashed_messages()
                return render_template("friend/add_friend.html", suggested_friends=suggested_friends)

            # Check if trying to add self
            if friend['_id'] == user_id:
                flash("You cannot add yourself as a friend")
                get_flashed_messages()
                return render_template("friend/add_friend.html", suggested_friends=suggested_friends)

            # Check if already friends
            if any(f.get('friend_id') == friend['_id'] for f in user.get('friends', [])):
                flash("You are already friends with this user")
                get_flashed_messages()
                return render_template("friend/add_friend.html", suggested_friends=suggested_friends)

            # Add friend logic
            current_time = datetime.datetime.now()
            db.new_user.update_one(
                {'_id': user_id},
                {'$push': {'friends': {
                    'friend_id': friend['_id'],
                    'created_on': current_time
                }}}
            )

            db.new_user.update_one(
                {'_id': friend['_id']},
                {'$push': {'friends': {
                    'friend_id': user_id,
                    'created_on': current_time
                }}}
            )

            flash("Friend added successfully")
            get_flashed_messages()
            return redirect(url_for("friendlist_bp.view_friends"))

    except Exception as e:
        print(f"Full error adding friend: {traceback.format_exc()}")
        flash(f"An error occurred: {str(e)}")
        get_flashed_messages()
        return redirect(url_for("friendlist_bp.add_friend"))

    return render_template("friend/add_friend.html", suggested_friends=suggested_friends)

@friendlist_bp.route("/delete-friend/<friend_id>")
# Function to delete a friend
def delete_friend(friend_id):
    try:
        db = get_NoSQLdb()
        
        user_id = session["_id"]  # Get the user_id from the session

        # Check if the friend exists
        friend = db.new_user.find_one({'_id': friend_id})

        if friend is None:
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
        return redirect(url_for("friendlist_bp.view_friends"))

    except Exception as e:
        print(f"Error: {e}")
        return f"Error deleting friend: {e}"