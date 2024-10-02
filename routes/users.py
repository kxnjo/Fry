from flask import Blueprint, jsonify, render_template, request, url_for, redirect, session
import mysql.connector
import config
import hashlib
import json
from datetime import date

# Create a Blueprint object
user_bp = Blueprint("user_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


def getUserNum(cur):
    cur.execute("SELECT * from user;")
    return len(cur.fetchall())


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


# == USER ROUTES ==
@user_bp.route("/user-count", methods=["GET", "POST"])
def user_count():
    conn = create_connection()
    cur = conn.cursor()
    return jsonify(getUserNum(cur))


# TODO: CREATE SESSION, ENABLE PERSISTENT LOGIN
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
                "SELECT user_id, username, password FROM user WHERE email = %s OR username = %s",
                (username_email, username_email),
            )
            user = cur.fetchall()[0] # there should only be ONE username
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
            return f"Error creating table: {e}"
            
    elif request.method == "GET":
        # do nothing i guess,, idk what else to do,, load up the page?? :P
        print("visited login page")

    return render_template("user/login.html", login_notif=notif)


# TODO: CREATE SESSION, ENABLE PERSISTENT LOGIN
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
                uid = f"u{getUserNum(cur) + 1}"
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


# TODO: FORGET PASSWORD !!!!!
@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        print("POST")
    elif request.method == "GET":
        print("GET")
    return render_template("user/forgot.html")

# TODO: LOG OUT !!!!!!!
@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))
