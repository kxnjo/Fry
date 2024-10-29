from flask import Blueprint, jsonify, render_template, request, url_for, redirect, session, flash
import mysql.connector

from dotenv import load_dotenv
import os

load_dotenv('config.env')
import hashlib
import json
from datetime import date
from auth_utils import login_required  # persistent login

# integrating everyone's parts
from mysql_routes.review import user_written_reviews
from mysql_routes.owned_game import get_owned_game
from mysql_routes.friend import get_dashboard_mutual_friends
from mysql_routes.game import getGameNum, getGames, get_all_games

# mongo
from mongo_cfg import get_NoSQLdb

# Create a Blueprint object
user_bp = Blueprint("user_bp", __name__)


# db connections
def create_connection():
    """
    Create and return a connection to the MySQL database.
    
    Returns:
    mysql.connector.connection.MySQLConnection: A connection object to the database.
    """
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

# MONGO connections
@user_bp.route('/test-db-connection')
def mongo_connection():

    db = get_NoSQLdb()

    if db is None:
        return "Database not initialized!!", 500
    try:
        user_collection = db["user"]

        # Retrieve all documents
        documents = user_collection.find()

        all_users = []
        # Iterate through documents and print them
        for doc in documents:
            all_users.append({
                "user_id": doc["user_id"],
                "username": doc["username"],
                "email": doc["email"],
                "password": doc["password"],
                "created_on": doc["created_on"]
            })

        return f"Successfully connected to MongoDB. all_users: {all_users}", 200
    except Exception as e:
        return f"Failed to connect to MongoDB: {e}", 500


# other functions for accessiblity
def getUserNum():
    """
    Get the total number of users in the database.
    
    Returns:
    int: The total number of users.
    """
    return len(getUsers())


def checkUser(cur, name, email):
    """
    Check if a username or email already exists in the database.
    
    Args:
    cur (mysql.connector.cursor.MySQLCursor): The database cursor.
    name (str): The username to check.
    email (str): The email to check.
    
    Returns:
    dict: A dictionary containing message, status, and uniqueness flag.
    """
    msg, status = "", ""
    unique = True

    

    # # Check for existing username
    # cur.execute(
    #     """
    #     SELECT user_id 
    #     FROM user 
    #     WHERE username = %s
    # """,
    #     (name,),
    # )
    # user_by_name = cur.fetchall()

    # # if someone already registered username
    # if len(user_by_name) > 0:
    #     msg = "Username is already taken! Please choose a different username."
    #     status = "warning"
    #     unique = False

    #     return {"msg": msg, "status": status, "unique": unique}

    # # Check for existing email
    # cur.execute(
    #     """
    #     SELECT user_id 
    #     FROM user 
    #     WHERE email = %s
    # """,
    #     (email,),
    # )
    # user_by_email = cur.fetchall()

    # # if someone already registered email
    # if len(user_by_email) > 0:
    #     msg = "Email is already registered! Please use a different email."
    #     status = "warning"
    #     unique = False

    #     return {"msg": msg, "status": status, "unique": unique}

    # return {"msg": msg, "status": status, "unique": unique}


def getUsers(start=0, end=10):
    """
    Get a list of users within a specified range.
    
    Args:
    start (int): The starting index.
    end (int): The ending index.
    
    Returns:
    list: A list of user dictionaries.
    """
    # MONGO = = =
    user_collection = db["user"]

    # Retrieve all documents
    user_documents = user_collection.find()

    all_users = []
    # Iterate through documents and print them
    for doc in user_documents:
        all_users.append({
            "user_id": doc["user_id"],
            "username": doc["username"],
            "email": doc["email"],
            "password": doc["password"],
            "created_on": doc["created_on"]
        })

    return all_users

    
    # MYSQL = = =
    # start connection
    # conn = create_connection()
    # if conn is None:
    #     return "Failed to connect to database"
    # try:
    #     cur = conn.cursor(dictionary=True)
    #     # execute query
    #     cur.execute(
    #         """
    #             SELECT * FROM (
    #                 SELECT user_id, username, email, created_on, role, 
    #                 ROW_NUMBER() OVER (ORDER BY user_id) as row_num 
    #                 FROM user) as temp_table
    #             WHERE row_num > %s AND row_num <= %s
    #         """,
    #         (start, end),
    #     )
    #     allUsers = cur.fetchall()

    #     # close connection
    #     cur.close()
    #     conn.close()

    #     return allUsers

    # except mysql.connector.Error as e:
    #     print(f"Error: {e}")
    #     return f"Error retrieving table: {e}"


def getUser(user_id):
    """
    Get user details by user ID.
    
    Args:
    user_id (str): The ID of the user.
    
    Returns:
    dict: A dictionary containing user details.
    """
    user = {}
    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute(
            """
                SELECT user_id, username, email
                FROM user 
                WHERE user_id = %s
            """,
            (user_id,),
        )
        user = cur.fetchall()[0]

        # close connection
        cur.close()
        conn.close()

        return user

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"


def checkuid(uid):
    """
    Check if a user ID exists in the database.
    
    Args:
    uid (str): The user ID to check.
    
    Returns:
    list: A list of matching user IDs.
    """
    userlist = []
    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute(
            """
            SELECT user_id 
            FROM user 
            WHERE user_id = %s
        """,
            (uid,),
        )
        userlist = cur.fetchall()

        # close connection
        cur.close()
        conn.close()

        return userlist

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"


def getuid():
    """
    Generate a new unique user ID.
    
    Returns:
    str: A new unique user ID.
    """
    uid = getUserNum() + 1

    while len(checkuid(f"u{uid}")) != 0:
        uid += 1

    return f"u{uid}"


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"

        try:
            cur = conn.cursor(dictionary=True)

            # handle the fields retrieved, make sure that it aligns with db
            username_email = request.form["username_email"]
            password = request.form["password"]

            # hash the password
            hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

            # Execute the SQL statement
            cur.execute(
                """
                    SELECT user_id, username, password, role 
                    FROM user 
                    WHERE email = %s OR username = %s
                """,
                (username_email, username_email),
            )
            user = cur.fetchone()
            cur.close()
            conn.close()

            if not user or user["password"] != hashed_input_password:
                flash("Incorrect username/password", "danger")
                return redirect(url_for("user_bp.login"))

            # save to session
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("home"))

        except mysql.connector.Error as e:
            flash(f"Error retrieving table: {e}", "danger")
            return redirect(url_for("user_bp.login"))

    return render_template("user/login.html")


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)

            # handle the fields retrieved, make sure that it aligns with db
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]

            # check if there is no existing user with same username/email
            checkUnique = checkUser(cur, name, email)

            if not checkUnique["unique"]:
                flash(checkUnique["msg"], checkUnique["status"])
                return redirect(url_for("user_bp.register"))

            else:
                # other details
                uid = getuid()

                role = "user"
                created_on = date.today()
                # hash the password
                hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

                # table query
                create_table_query = """
                    INSERT INTO user (user_id, username, email, password, created_on, role) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                # Execute the SQL statement
                cur.execute(
                    create_table_query,
                    (uid, name, email, hashed_input_password, created_on, role),
                )
                conn.commit()

                return redirect(
                    url_for("user_bp.login")
                )  # send them back to login page

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error creating table: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template("user/register.html")


@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    """Handle password reset."""
    if request.method == "POST":
        # Retrieve form data
        username_email = request.form["username_email"]
        password = request.form["password"]
        # hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # start connection
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)
            # execute query
            cur.execute(
                """
                    UPDATE user SET password = %s
                    WHERE username = %s OR email = %s
                """,
                (
                    hashed_password,
                    username_email,
                    username_email,
                ),
            )
            # save to db
            conn.commit()

            # close connection
            cur.close()
            conn.close()

            return redirect(url_for("user_bp.login"))

        except mysql.connector.Error as e:
            print(f"Error: {e}")
            return f"Error retrieving table: {e}"

    return render_template("user/forgot.html")


@user_bp.route("/logout")
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for("home"))


@user_bp.route("/dashboard")
@login_required
def dashboard():
    """Display user or admin dashboard."""
    if session["role"] == "admin":
        # Get the current page number, set default to start from 1
        filter_type = request.args.get("filter_type", "accounts", type=str)
        page = request.args.get("page", 1, type=int)

        # Default variables for pagination
        all_users = []
        all_games = []

        # User pagination logic
        all_users_num = getUserNum()  # Retrieve the total number of users
        user_num_per_page = 10
        user_total_pages = (
            all_users_num + user_num_per_page - 1
        ) // user_num_per_page  # Calculate total pages

        # Paginate the users
        user_start = (page - 1) * user_num_per_page
        user_end = user_start + user_num_per_page
        all_users = getUsers(user_start, user_end)  # Get users for current page

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
        curr_id = request.args.get("user_id", session["user_id"], type=str)
        games, user_reviews, mutual_friends = None, None, None

        # get user details
        user = getUser(curr_id)

        # INSERT GAMES OWNED
        games = get_owned_game(curr_id)

        # INSERT REVIEWS CODE TO DISPLAY REVIEWS LIST MADE BY USER
        user_reviews = user_written_reviews(curr_id)

        # INSERT MUTUAL FRIENDS LIST
        if curr_id == session["user_id"]:
            mutual_friends = get_dashboard_mutual_friends(curr_id, curr_id)
        else:
            mutual_friends = get_dashboard_mutual_friends(curr_id, session["user_id"])


        return render_template(
            "user/user_dashboard.html",
            user=user,
            games=games,
            user_reviews=user_reviews,
            mutual_friends=mutual_friends,
        )

    elif session["role"] == "developer":
        games = get_all_games()[:10]

        return render_template("user/developer_dashboard.html", games=games)


@user_bp.route("/create-user", methods=["POST"])
@login_required
def create_user():
    """Handle user registration."""
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)

            # handle the fields retrieved, make sure that it aligns with db
            name = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            role = request.form['role']

            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                print("it does not match or sth")
                return redirect(request.referrer or url_for("user_bp.dashboard"))

            # check if there is no existing user with same username/email
            checkUnique = checkUser(cur, name, email)

            if not checkUnique["unique"]:
                flash(checkUnique["msg"], checkUnique["status"])
                return redirect(url_for("user_bp.register"))

            else:
                # other details
                uid = getuid()

                created_on = date.today()
                # hash the password
                hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

                # table query
                create_table_query = """
                    INSERT INTO user (user_id, username, email, password, created_on, role) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                # Execute the SQL statement
                cur.execute(
                    create_table_query,
                    (uid, name, email, hashed_input_password, created_on, role),
                )
                conn.commit()
                print(f"successfully created user {name}")

                return redirect(request.referrer or url_for("user_bp.dashboard"))

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error creating table: {e}"
        finally:
            cur.close()
            conn.close()

    return redirect(request.referrer or url_for("user_bp.dashboard"))

@user_bp.route("/edit-user/<string:user_id>", methods=["POST"])
@login_required
def edit_user(user_id):
    """Edit user details."""
    # Retrieve form data
    username = request.form["username"]
    email = request.form["email"]

    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute(
            """
                UPDATE user SET username = %s, email = %s 
                WHERE user_id = %s
            """,
            (
                username,
                email,
                user_id,
            ),
        )

        # save to db
        conn.commit()

        # close connection
        cur.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"

    return redirect(request.referrer or url_for("user_bp.dashboard"))


@user_bp.route("/delete_user/<string:user_id>")
@login_required
def delete_user(user_id):
    """Delete a user account."""
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)

        # delete user
        cur.execute(
            """
                DELETE FROM user
                WHERE user_id = %s
            """,
            (user_id,),
        )

        # save to db
        conn.commit()

        # close connection
        cur.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"

    if user_id == session["user_id"]:
        session.clear()
        return redirect(url_for("home"))

    return redirect(request.referrer or url_for("user_bp.dashboard"))
