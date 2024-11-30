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
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
from mysql_routes.game import getGameNum, getGames, get_all_games

# Create a Blueprint object
user_bp = Blueprint("user_bp", __name__)

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

# MARK: custom functions
def generate_id():
    # Retrieve all _ids that match the pattern `u<number>`
    existing_ids = db.new_user.find(
        {"_id": {"$regex": "^u\\d+$"}},     # find for id values with u<number>
        {"_id": 1}                          # retrieve only id
    )
    
    # Extract numeric parts of _ids into a sorted list
    used_numbers = sorted(int(doc["_id"][1:]) for doc in existing_ids) # loop through all ids and sort values
    
    # Find the lowest available ID by checking for gaps
    new_id_number = used_numbers[-1] + 1

    # Format and Return the new ID
    return f"u{new_id_number}"


# MARK: LOGIN
@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":

        # handle the fields retrieved, make sure that it aligns with db
        username_email = request.form["username_email"].strip()
        password = request.form["password"].strip()
        # validate fields
        if not username_email or not password:
            flash("Username/email and password are required.", "danger")
            return redirect(url_for("user_bp.login"))
        
        try:
            # Ensure db.new_user is initialized
            db = get_db()  
            if db.new_user is None:
                raise RuntimeError("User collection not initialized!")

            if "@" in username_email:
                query = {"email": username_email}
            else:
                query = {"username": username_email}
            
            # Retrieve user from database
            user = db.new_user.find_one(query, {"_id": 1, "username": 1, "role": 1, "password": 1}) # get only id, username, role and password fields

            # Check user existence and password
            if not user:
                flash("Invalid username or email.", "danger")
                return redirect(url_for("user_bp.login"))

            # Compare hashed password (use bcrypt)
            if not bcrypt.checkpw(password.encode(), user["password"].encode()):
                flash("Incorrect password.", "danger")
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
            return redirect(url_for("user_bp.login"))
            

    # if the method is GET instead, load the html
    return render_template("user/login.html")

# MARK: REGISTER ACCOUNT
@user_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if request.method == "POST":

        # Ensure db.new_user is initialized
        db = get_db()  

        # get user details: name, email and password
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # hash the password
        bcrypt_hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try: 
            new_user = {
                "_id": generate_id(),   # auto generate a unique id
                "username": name,
                "email": email, 
                "password": bcrypt_hashed_password,
                "role": "user",         # default create new user role only. admin + developer created by admin
                "created_on": datetime.now().date().isoformat()
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

# MARK: FORGET PASSWORD
@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    """Handle password reset."""
    if request.method == "POST":

        # Ensure db is initialized
        db = get_db()  
            
        # Retrieve form data
        username_email = request.form["username_email"]
        password = request.form["password"]
        # hash the password
        bcrypt_hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            result = db.new_user.update_one(
                {"$or": [{"username": username_email}, {"email": username_email}]},  # filter to find each user by either username or email
                {"$set": {"password": bcrypt_hashed_password}}
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

# MARK: LOGOUT
@user_bp.route("/logout")
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for("home"))


# MARK: DASHBOARD
@user_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()

    """Display user or admin dashboard."""

    # print(f"this is current role: {session['role']}")
    if session["role"] == "admin":
        # Retrieve filter type (accounts or games) and page number from query params
        filter_type = request.args.get("filter_type", "accounts", type=str)
        page = request.args.get("page", 1, type=int)            # get current page number, default to first page
        items_per_page = 10                                     # set the number of items per page
        sort_field = request.args.get("sort_field", "_id")      # get field to sort, default to _id
        sort_order = int(request.args.get("sort_order", 1))     # get sort order, 1 for ascending, -1 for descending
        search_query = request.args.get("search", "")           # get search value, default to nothing
 
        users, games = [], []
        user_total_pages, game_total_pages = 0, 0

        if filter_type == "accounts":
            query = {}
            if search_query:
                query = {
                    "$or": [
                        {"username": {"$regex": search_query, "$options": "i"}},    # search by username, NOT case sensitive (options 'i')
                        {"email": {"$regex": search_query, "$options": "i"}},       # search by email, NOT case sensitive (options 'i')
                    ]
                }

            total_users = db.new_user.count_documents(query)    # get the number of users
            users = list(
                db.new_user.find(query)
                .sort({sort_field: sort_order})         # sort by field 
                .skip((page - 1) * items_per_page)      # for pagination, start at x entry
                .limit(items_per_page)                  # for pagination, stop at x entry (depending on size)
            )
            user_total_pages = (total_users + items_per_page - 1) // items_per_page

        elif filter_type == "games":
            query = {}
            if search_query:
                query = {"title": {"$regex": search_query, "$options": "i"}}

            total_games = db.new_game.count_documents(query)
            games = list(
                db.new_game.find(query)
                .sort({sort_field: sort_order})
                .skip((page - 1) * items_per_page)
                .limit(items_per_page)
            )
            game_total_pages = (total_games + items_per_page - 1) // items_per_page

        return render_template(
            "user/admin_dashboard.html",
            users=users,
            games=games,
            filter_type=filter_type,
            page=page,
            user_total_pages=user_total_pages,
            game_total_pages=game_total_pages,
            sort_field=sort_field,
            sort_order=sort_order,
            search_query=search_query,
            max=max,    # because jinja dont have built-in function for max/min, so js pass in from python flask
            min=min,    # because jinja dont have built-in function for max/min, so js pass in from python flask
        )

    elif session["role"] == "user":
        games, user_reviews, mutual_friends = None, None, None

        curr_id = request.args.get("_id", session["_id"], type=str)

        # get user details
        query = {"_id": curr_id}
        user = db.new_user.find_one(query)

        # print("this is user", user)
        if "image" in user:
            encoded_image = user["image"]
        else:
            encoded_image = "https://static.vecteezy.com/system/resources/previews/023/465/688/non_2x/contact-dark-mode-glyph-ui-icon-address-book-profile-page-user-interface-design-white-silhouette-symbol-on-black-space-solid-pictogram-for-web-mobile-isolated-illustration-vector.jpg"

        # INSERT GAMES OWNED
        games = get_owned_game(curr_id) # TODO: UPDAGTE TO MONGO VERSION

        # INSERT REVIEWS CODE TO DISPLAY REVIEWS LIST MADE BY USER
        user_reviews = user_written_reviews(curr_id) # TODO: UPDAGTE TO MONGO VERSION

        # INSERT MUTUAL FRIENDS LIST
        if curr_id == session["_id"]:
            mutual_friends = get_dashboard_mutual_friends(curr_id, curr_id) # TODO: UPDAGTE TO MONGO VERSION
        else:
            mutual_friends = get_dashboard_mutual_friends(curr_id, session["_id"]) # TODO: UPDAGTE TO MONGO VERSION


        return render_template(
            "user/user_dashboard.html",
            user=user,
            games=games,
            user_reviews=user_reviews,
            mutual_friends=mutual_friends,
            profile_pic = encoded_image
        )

    elif session["role"] == "developer":
        games = db.new_game.find()[:10] # TODO: UPDAGTE TO MONGO VERSION

        all_games = []
        for game in games:            
            print(f"this is indiv game! {game}")
            all_games.append(game)

        return render_template("user/developer_dashboard.html", games=all_games)


# MARK: ADMIN CREATE USER
# TODO: roadblock- i dont know how to display error message while modal is open heh
@user_bp.route("/create-user", methods=["POST"])
@login_required
def create_user():
    """Handle user registration."""
    if request.method == "POST":
        
        # Ensure db is initialized
        db = get_db()  
        
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role') 
        confirm_password = request.form['confirm_password']

        # Password confirmation check
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})


        new_user = {
            "_id": generate_id(),
            "username": name,
            "email": email,
            "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "role": role,
            "created_on": datetime.now().date().isoformat()
        }

        try:
            result = db.new_user.update_one(
                {"or": [{"username": name}, {"email": email}]},
                {"$setOnInsert": new_user}, # only insert if the document does not already have an insert
                upsert=True
            )

            # Check if the user was inserted or already existed
            if result.upserted_id: # This is set if a new document was inserted
                flash(f"User {name} created successfully!", "success")
                return redirect(url_for("user_bp.dashboard"))
            else:
                flash("User already exists! Please use another username/email.", "warning")
                return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})


        except pymongo.errors.PyMongoError as e:
            flash(f"An unknown error occurred: {e}", "danger")
            return render_template("user/admin_dashboard.html", show_create_modal=True, form_data={"username": name, "email": email, "role": role})

    # GET request: render the registration page normally
    return render_template("user/admin_dashboard.html")


# MARK: EDIT USER
@user_bp.route("/edit-user/<string:_id>", methods=["POST"])
@login_required
def edit_user(_id):
    """Edit user details."""

    # Ensure db is initialized
    db = get_db()

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


# MARK: DELETE USER
@user_bp.route("/delete_user/<string:_id>")
@login_required
def delete_user(_id):
    """Delete a user account."""

    # Ensure db is initialized
    db = get_db()

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
