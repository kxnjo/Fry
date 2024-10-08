from flask import Blueprint, jsonify, render_template, request, url_for, redirect, session
import mysql.connector
import config
import hashlib
import json
from datetime import date
from auth_utils import login_required  # persistent login

# integration
# from routes.game import get_all_games
from routes.review import xinhui
# Create a Blueprint object
user_bp = Blueprint("user_bp", __name__)
all_users_num = []

def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

def getUserNum():
    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute("SELECT * from user;")
        total = cur.fetchall()
        print(f"found this many users {len(total)}")

        # close connection
        cur.close()
        conn.close()
        return len(total)

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"
def checkUser(cur, name, email):
    print("checking user")
    # Check for existing username
    cur.execute("SELECT user_id FROM user WHERE username = %s", (name,))
    user_by_name = cur.fetchall()
    
    if len(user_by_name) >   0:
        return {
            "status": False,
            "response": {
                "status": "danger", 
                "message": "Username is already taken! Please choose a different username."
            }
        }

    # Check for existing email
    cur.execute("SELECT user_id FROM user WHERE email = %s", (email,))
    user_by_email = cur.fetchall()

    if len(user_by_email) > 0:
        return {
            "status": False,
            "response": {
                "status": "danger", 
                "message": "Email is already registered! Please use a different email."
            }
        }

    return {
        "status": True,
        "response": {
            "status": "success", 
            "message": "Username and email are unique."
        }
    }
def getAllUsers(start = 0, end = 10):
    allUsers = []
    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        print(f"this is start: {start} and end {end}")
        cur.execute("""SELECT * FROM (
                    SELECT user_id, username, email, created_on, ROW_NUMBER() OVER (ORDER BY user_id) as row_num FROM user) as temp_table
                    WHERE row_num > %s AND row_num <= %s""", (start, end))
        allUsers = cur.fetchall()

        # close connection
        cur.close()
        conn.close()
        
        return allUsers

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"
def getUser():
    user = {}
    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute("SELECT user_id, username, email from user WHERE user_id = %s", (session["user_id"],))
        user = cur.fetchall()[0]

        # close connection
        cur.close()
        conn.close()
        
        return user

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    notif = request.args.get("login_notif")

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

            print("before print db")
            # Execute the SQL statement
            cur.execute(
                "SELECT user_id, username, password, role FROM user WHERE email = %s OR username = %s",
                (username_email, username_email),
            )
            users = cur.fetchall()
            print(users, len(users))
            if len(users) == 0: # if user does not exist
                notif = {
                    "status": "danger", 
                    "message": "Incorrect username/password"
                }   # there should only be ONE username
                return redirect(url_for("user_bp.login", login_notif=notif)) # if there is error, return error
            else:
                user = users[0]
            print("retrieved details")

            # close connection
            cur.close()
            conn.close()
            print("closed connection")

            print(user)

            if user and user["password"] == hashed_input_password:
                print("the user email and password correct")
                # save to session
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                
                return redirect(url_for("home"))
            else:
                print("the user password wrong")
                notif = {
                    "status": "danger", 
                    "message": "Incorrect username/password"
                }

            return redirect(url_for("user_bp.login", login_notif=notif)) # if there is error, return error

        except mysql.connector.Error as e:
            print(f"Error: {e}")
            return f"Error retrieving table: {e}"
            
    elif request.method == "GET":
        # do nothing i guess,, idk what else to do,, load up the page?? :P
        print("visited login page")

    return render_template("user/login.html", login_notif=notif)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    notif = request.args.get("create_notif")
    print("\n\nthis is notif")
    print(notif)

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
            status = checkUnique["status"]
            responsnotife = checkUnique["response"]

            if status:
                # other details
                uid = f"u{getUserNum() + 1}"
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

                return redirect(url_for("user_bp.login", create_notif=notif)) # send them back to login page #TODO: display notif message

            else:
                print("sending back to register")
                return redirect(url_for("user_bp.register", create_notif=notif))

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error creating table: {e}"
        finally:
            cur.close()
            conn.close()
    if request.method == "GET":
        print("ITS GETTING")
        print(type(notif))

    return render_template("user/register.html", create_notif=notif)


@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
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
            cur.execute("""
                UPDATE user SET password = %s
                WHERE username = %s OR email = %s""", 
                (hashed_password, username_email, username_email,)
            )
            print(cur.fetchall())
            # save to db
            conn.commit()
            print("user pw updated")

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
    session.clear()
    return redirect(url_for('home'))


# TODO: USER DASHBOARD, 1 for admin 1 for regular user (IN PROGRESS)
@user_bp.route("/dashboard")
@login_required
def dashboard():
    if session["role"] == "admin":
        # retrieve the total number of users ONCE !
        all_users_num = getUserNum()

        # get the current page number, set default number to start from 1
        page = request.args.get('page', 1, type=int) 
        print(f"i am page {page}, all_users_num {all_users_num}")

        # get the total amt of pages
        users_per_page = 10
        total_pages = all_users_num // users_per_page + 1 
        print(f"this is total pages {total_pages}")

        # Paginate the users from the cache
        start = (page - 1) * users_per_page
        end = start + users_per_page
        all_users = getAllUsers(start, end)

        return render_template("user/admin_dashboard.html", users = all_users, page = page, total_pages = total_pages)

    elif session["role"] == "user":
        user = getUser()

        # TODO: INSERT GAMES OWNED
            # need: game title, (reference however is displayed in games)
        # games = get_all_games()[:5] TODO: CHANGE THIS TO OWNED GAMES
        # print(games)

        # TODO: INSERT REVIEWS CODE TO DISPLAY REVIEWS LIST MADE BY USER,, 
            # need: game title, review, redirect to game review button ???
        user_reviews = xinhui()
        # TODO: INSERT MUTUAL FRIENDS LIST
            # need: friend username, redirect to user account button

        return render_template("user/user_dashboard.html", user = user, games=[], user_reviews = user_reviews)
    

@user_bp.route('/edit-user/<string:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    # Retrieve form data
    username = request.form['username']
    email = request.form['email']

    # start connection
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query
        cur.execute("""
            UPDATE user SET username = %s, email = %s 
            WHERE user_id = %s""", 
            (username, email, session["user_id"],)
        )

        # save to db
        conn.commit()

        # close connection
        cur.close()
        conn.close()

        print("user updated successfully")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"

    return redirect(url_for('user_bp.dashboard'))


# TODO: DELETE USER, delete all related relations
@user_bp.route("/delete_user/<string:user_id>", methods=['POST'])
@login_required
def delete_user(user_id):
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        # execute query

        # TODO: delete all friend relations
        # TODO: delete all related relations

        # delete user
        cur.execute("""
            DELETE FROM user
            WHERE user_id = %s""", 
            (user_id,)
        )

        # save to db
        conn.commit()

        # close connection
        cur.close()
        conn.close()

        print("user deleted successfully")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving table: {e}"

    session.clear()
    return redirect(url_for('home'))
