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

        # Retrieve the user's friends with a single projection
        user = db.new_user.find_one({'_id': user_id}, {'friends': 1})
        if not user:
            return "User not found", 404

        # Get friend IDs
        friend_ids = [friend.get('friend_id') for friend in user.get('friends', [])]
        
        # Fetch friends in a single query with limited fields
        friends = list(db.new_user.find(
            {"_id": {"$in": friend_ids}}, 
            {
                '_id': 1, 
                'username': 1, 
                'owned_games': 1, 
                'wanted_games': 1, 
                'friends': 1,
            }
        ))

        # Collect all game IDs to fetch in bulk
        owned_game_ids = []
        wanted_game_ids = []
        for friend in friends:
            owned_game_ids.extend([game['game_id'] for game in friend.get('owned_games', [])])
            wanted_game_ids.extend([game['game_id'] for game in friend.get('wanted_games', [])])

        # Fetch game titles in bulk
        owned_games_dict = {game['_id']: game['title'] for game in 
            db.new_game.find({'_id': {'$in': list(set(owned_game_ids))}}, {'title': 1})}
        wanted_games_dict = {game['_id']: game['title'] for game in 
            db.new_game.find({'_id': {'$in': list(set(wanted_game_ids))}}, {'title': 1})}

        # Prepare friend data
        friend_data = []
        for friend in friends:
            # Process owned games
            owned_game_titles = [
                owned_games_dict.get(game['game_id'], 'Unknown') 
                for game in friend.get('owned_games', [])
            ]

            # Process wanted games
            wanted_game_titles = [
                wanted_games_dict.get(game['game_id'], 'Unknown') 
                for game in friend.get('wanted_games', [])
            ]

            # Find mutual friends
            friend_friend_ids = {f.get('friend_id') for f in friend.get('friends', [])}
            user_friend_ids = set(friend_ids)
            mutual_friend_ids = friend_friend_ids & user_friend_ids

            # Fetch mutual friends in a single query
            mutual_friends = list(db.new_user.find(
                {'_id': {'$in': list(mutual_friend_ids)}}, 
                {'_id': 1, 'username': 1}
            ))

            friend_data.append({
                'friend_id': friend['_id'],
                'friendship_date': next((f.get('friendship_date') for f in friend.get('friends', []) ), 'Unknown'),
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
            current_time = datetime.datetime.now().date().isoformat()
            db.new_user.update_one(
                {'_id': user_id},
                {'$push': {'friends': {
                    'friend_id': friend['_id'],
                    'friendship_date': current_time
                }}}
            )

            db.new_user.update_one(
                {'_id': friend['_id']},
                {'$push': {'friends': {
                    'friend_id': user_id,
                    'friendship_date': current_time
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