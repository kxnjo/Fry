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
from datetime import date
from auth_utils import login_required  # persistent login

# MongoDB setup
import mongo_cfg

# integrating everyone's parts
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object
user_bp = Blueprint("user_bp", __name__)

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


# MONGO connections
@user_bp.route('/test-db-connection')
def mongo_connection():
    # Ensure db.new_user is initialized
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    try:
        # Retrieve all documents
        documents = db.new_user.find()

        # Iterate through documents and print them
        all_users = []
        for doc in documents:
            all_users.append({
                "_id": doc["_id"],
                "username": doc["username"],
                "email": doc["email"],
                "password": doc["password"],
                "created_on": doc["created_on"]
            })

        for doc in documents:
            print(doc)

        return f"Successfully connected to MongoDB. all_users: {all_users}", 200
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500

# other functions for accessiblity
def get_all_users(start=0, end=10):
    """
    Get a list of users within a specified range.
    
    Args:
    start (int): The starting index.
    end (int): The ending index.
    
    Returns:
    list: A list of user dictionaries.
    """
    # MONGO = = =
    # Retrieve all documents
    # Ensure db.new_user is initialized
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500
        
    user_documents = db.new_user.find()

    all_users = []
    # Iterate through documents and print them
    for doc in user_documents:
        all_users.append({
            "_id": doc["_id"],
            "username": doc["username"],
            "email": doc["email"],
            "password": doc["password"],
            "created_on": doc["created_on"],
            "role": doc["role"]
        })

    return all_users

def get_user_num():
    """
    Get the total number of users in the database.
    
    Returns:
    int: The total number of users.
    """
    return len(get_all_users())

def generate_id():
    # Retrieve all _ids that match the pattern `u<number>`
    existing_ids = db.new_user.find(
        {"_id": {"$regex": "^u\\d+$"}}, 
        {"_id": 1}
    )
    
    # Extract numeric parts of _ids into a sorted list
    used_numbers = sorted(int(doc["_id"][1:]) for doc in existing_ids)
    
    # Find the lowest available ID by checking for gaps
    new_id_number = used_numbers[-1] + 1

    # Format the new ID
    new__id = f"u{new_id_number}"
    return new__id

def get_user(name="", email="", uid=""):
    """
    Get user details by user ID.
    
    Args:
    name (str): The user's username.
    email (str): The user's email address
    uid (str): The user's unique id (u<id>)
    
    Returns:
    dict: A dictionary containing user details.
    """

    # Ensure db.new_user is initialized
    db = initialize_database()  
    if db.new_user is None:
        return "Collection not initialized!!", 500

    try:
        query = {"$or": [{"username": name}, {"email": email}, {"_id": uid}]}
        user = db.new_user.find_one(query)

        return user

    except pymongo.error.PyMongoError as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":

        # Ensure db.new_user is initialized
        db = initialize_database()  
        if db.new_user is None:
            return "Collection not initialized!!", 500

        try:
            # handle the fields retrieved, make sure that it aligns with db
            username_email = request.form["username_email"]
            password = request.form["password"]

            # hash the password
            hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

            # Execute the Mongodb statement
            user = get_user(username_email, username_email, "") # can use either username or email

            # error handling: if username/email does not exist, user == None, return error. If password wrong also, return error.
            if not user or user["password"] != hashed_input_password:
                flash("Incorrect username/password", "danger")
                return redirect(url_for("user_bp.login"))

            # save to session
            session["_id"] = user["_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            print("user successfully logged in!")
            return redirect(url_for("home"))

        except pymongo.errors.PyMongoError as e:
            # Handle any pymongo-related error
            flash(f"An unknown error occurred: {e}", "danger")
            print(f"An unknown error occurred: {e}")
            return redirect(url_for("user_bp.login"))
            

    # if the method is GET instead, load the html
    return render_template("user/login.html")


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if request.method == "POST":

        # Ensure db.new_user is initialized
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500

        # handle the fields retrieved, make sure that it aligns with db
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # hash the password
        hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

        try: 
            new_user = {
                "_id": generate_id(),
                "username": name,
                "email": email, 
                "password": hashed_input_password,
                "role": "user",
                "created_on": date.today().isoformat()
            }
            db.new_user.insert_one(new_user)
            print(f"Create user {name} success !")

            return redirect( url_for("user_bp.login") )  # send them back to login page
            
        except pymongo.errors.DuplicateKeyError:
            flash("User exists! Please use another username/password", "warning")
            return redirect(url_for("user_bp.register"))

        except pymongo.errors.PyMongoError as e:
            # Handle any pymongo-related error
            flash(f"An unknown error occurred: {e}", "danger")
            print(f"An unknown error occurred: {e}")
            return redirect(url_for("user_bp.register"))
                
    # if the method is GET instead, load the html
    return render_template("user/register.html")


@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    """Handle password reset."""
    if request.method == "POST":

        # Ensure db is initialized
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500
            
        # Retrieve form data
        username_email = request.form["username_email"]
        password = request.form["password"]
        # hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            result = db.new_user.update_one(
                {"$or": [ {"username": username_email}, {"email": username_email}]},  # filter to find each user by either username or email
                {"$set": {"password": hashed_password}}
            )

            if result.modified_count > 0:
                print(f"successfully updated password for {username_email}")
                return redirect(url_for("user_bp.login"))
            else: 
                raise Exception("No document matched the filter. Password update failed.")

        except (pymongo.errors.PyMongoError, Exception) as e:
            print(f"Error: {e}")
            return redirect(url_for("user_bp.forgot"))
            
    # if the method is GET instead, load the html
    return render_template("user/forgot.html")


@user_bp.route("/logout")
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for("home"))


# TODO: DASHBOARD (maybe half done?? idk i havent fully tested it)
@user_bp.route("/dashboard")
@login_required
def dashboard():
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    """Display user or admin dashboard."""

    # print(f"this is current role: {session['role']}")
    if session["role"] == "admin":
        # Get the current page number, set default to start from 1
        filter_type = request.args.get("filter_type", "accounts", type=str)
        page = request.args.get("page", 1, type=int)

        # Default variables for pagination
        all_users = []
        all_games = []

        # User pagination logic
        all_users_num = get_user_num()  # Retrieve the total number of users
        user_num_per_page = 10
        user_total_pages = (
            all_users_num + user_num_per_page - 1
        ) // user_num_per_page  # Calculate total pages

        # Paginate the users
        user_start = (page - 1) * user_num_per_page
        user_end = user_start + user_num_per_page
        all_users = get_all_users(user_start, user_end)  # Get users for current page

        # Game pagination logic
        all_games_num = getGameNum()  # Retrieve the total number of games
        game_num_per_page = 50
        game_total_pages = (
            all_games_num + game_num_per_page - 1
        ) // game_num_per_page  # Calculate total pages

        # Paginate the games
        game_start = (page - 1) * game_num_per_page
        game_end = game_start + game_num_per_page
        all_games = getGames(game_start, game_end)  # Get games for current page

        return render_template(
            "user/admin_dashboard.html",
            users=all_users,
            user_total_pages=user_total_pages,
            games=all_games,
            game_total_pages=game_total_pages,
            page=page,  # Pass the current page to the template,
            filter_type=filter_type,
        )

    elif session["role"] == "user":
        curr_id = request.args.get("_id", session["_id"], type=str)
        games, user_reviews, mutual_friends = None, None, None

        # get user details
        user = get_user("", "", curr_id)
        # print("this is user", user)
        if "image" in user:
            encoded_image = user["image"]
        else:
            encoded_image = "https://static.vecteezy.com/system/resources/previews/023/465/688/non_2x/contact-dark-mode-glyph-ui-icon-address-book-profile-page-user-interface-design-white-silhouette-symbol-on-black-space-solid-pictogram-for-web-mobile-isolated-illustration-vector.jpg"

        # INSERT GAMES OWNED
        games = get_owned_game(curr_id)

        # INSERT REVIEWS CODE TO DISPLAY REVIEWS LIST MADE BY USER
        user_reviews = user_written_reviews(curr_id)

        # INSERT MUTUAL FRIENDS LIST
        if curr_id == session["_id"]:
            mutual_friends = get_dashboard_mutual_friends(curr_id, curr_id)
        else:
            mutual_friends = get_dashboard_mutual_friends(curr_id, session["_id"])


        return render_template(
            "user/user_dashboard.html",
            user=user,
            games=games,
            user_reviews=user_reviews,
            mutual_friends=mutual_friends,
            profile_pic = encoded_image
        )

    elif session["role"] == "developer":
        games = db.new_game.find()[:10]

        all_games = []
        for game in games:            
            print(f"this is indiv game! {game}")
            all_games.append(game)

        return render_template("user/developer_dashboard.html", games=all_games)


# TODO: roadblock- i dont know how to display error message while modal is open heh
@user_bp.route("/create-user", methods=["POST"])
@login_required
def create_user():
    """Handle user registration."""
    if request.method == "POST":
        
        # Ensure db is initialized
        db = initialize_database()  
        if db is None:
            return "Database not initialized!!", 500

        # Get the form data
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        hashed_input_password = hashlib.sha256(password.encode()).hexdigest()  # hash the password

        # Password confirmation check
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})

        # Check if username or email already exists
        if db.new_user.find_one({"$or": [{"username": name}, {"email": email}]}):
            flash("User exists! Please use another username/email", "warning")
            return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})

        # Proceed with creating the user if no errors
        try:
            new_user = {
                "_id": generate_id(),
                "username": name,
                "email": email, 
                "password": hashed_input_password,
                "role": role,
                "created_on": date.today().isoformat()
            }
            db.new_user.insert_one(new_user)
            print(f"Successfully created user {name}")
            return redirect(url_for("user_bp.dashboard"))

        except pymongo.errors.PyMongoError as e:
            flash(f"An unknown error occurred: {e}", "danger")
            return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})

    # GET request: render the registration page normally
    return render_template("user/admin_dashboard.html")


@user_bp.route("/edit-user/<string:_id>", methods=["POST"])
@login_required
def edit_user(_id):
    """Edit user details."""

    # Ensure db is initialized
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    # Retrieve form data
    username = request.form["username"]
    email = request.form["email"]
    updated_user = {
        "username": username,
        "email": email
    }

    # update profile picture
    profile_picture = request.files.get("profile-picture")
    if profile_picture and profile_picture.filename != '':
        print("Profile picture detected!")
        encoded_img = "data:image/jpeg;base64," + base64.b64encode(profile_picture.read()).decode("utf-8")  # Convert image to binary
        updated_user["image"] = encoded_img
    
    # print("Updated user document:", updated_user)

    try:
        result = db.new_user.update_one(
            {"_id": _id},  # filter to find user by _id
            {"$set": updated_user}
        )

        if result.modified_count > 0:
            print(f"successfully updated user details for {username}")
            return redirect(url_for("user_bp.dashboard"))
        else:
            print("No document matched the filter, or no changes were made.")
            flash("Update failed. No changes were made.", "danger")
            return redirect(url_for("user_bp.dashboard"))


    except (pymongo.errors.PyMongoError, Exception) as e:
        print(f"Error: {e}")
        return redirect(url_for("user_bp.dashboard"))

    return redirect(request.referrer or url_for("user_bp.dashboard"))


@user_bp.route("/delete_user/<string:_id>")
@login_required
def delete_user(_id):
    """Delete a user account."""

    # Ensure db is initialized
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500

    result = db.new_user.delete_one({"_id": _id})
    # Check if a document was deleted
    if result.deleted_count > 0:
        print("Document deleted successfully.")
    else:
        print("No document matched the filter.")

    if _id == session["_id"]:
        session.clear()
        return redirect(url_for("home"))

    return redirect(request.referrer or url_for("user_bp.dashboard"))
