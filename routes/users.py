from flask import Blueprint, jsonify, render_template, request
import mysql.connector
import config
import hashlib
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
    cur.execute(
        """
        SELECT * FROM user
        WHERE username = %s OR email = %s
    """,
        (name, email),
    )
    users = cur.fetchall()
    if len(users) != 0:
        print("username or email is not unique! please enter again.")
        return False

    print("no existing users with the same name and email~! proceed to create account")
    return True


# == USER ROUTES ==
@user_bp.route("/user-count", methods=["GET", "POST"])
def user_count():
    conn = create_connection()
    cur = conn.cursor()
    return jsonify(getUserNum(cur))

@user_bp.route("/login", methods=["GET", "POST"])
def login():
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
                "SELECT password FROM user WHERE email = %s OR username = %s",
                (username_email, username_email),
            )
            user = cur.fetchone()

            if user:
                if user["password"] == hashed_input_password:
                    response = {"message": "Login successful"}
                else:
                    response = {"message": "Incorrect password"}
            else:
                response = {"message": "Incorrect user/password"}

            return jsonify(response)

        except mysql.connector.Error as e:
            print(f"Error: {e}")
            return f"Error creating table: {e}"
        finally:
            cur.close()
            conn.close()

    elif request.method == "GET":
        # do nothing i guess,, idk what else to do,, load up the page?? :P
        print("visited login page")

    return render_template("user/login.html")


@user_bp.route("/register", methods=["GET", "POST"])
def register():
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

            # TODO: check if there is already an existing user
            if checkUser(cur, name, email):
                # other details
                uid = f"u{getUserNum(cur) + 1}"
                print("uid =", uid)
                created_on = date.today()
                print(f"created_on = {created_on}")
                # hash the password
                hashed_input_password = hashlib.sha256(password.encode()).hexdigest()

                # table query
                create_table_query = """
                    INSERT INTO user (user_id, username, email, password, created_on) 
                    VALUES (%s, %s, %s, %s, %s)
                """

                # Execute the SQL statement
                cur.execute(
                    create_table_query,
                    (uid, name, email, hashed_input_password, created_on),
                )
                conn.commit()

                return render_template("user/login.html")
            else:
                return jsonify("User or email exists! try again.")

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error creating table: {e}"
        finally:
            cur.close()
            conn.close()

    elif request.method == "GET":
        print("GET")
    return render_template("user/register.html")


@user_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        print("POST")
    elif request.method == "GET":
        print("GET")
    return render_template("user/forgot.html")
