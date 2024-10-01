from flask import Blueprint, render_template, request
import mysql.connector
import config
import datetime

# Create a Blueprint object
friendlist_bp = Blueprint("friendlist_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

@friendlist_bp.route("/view-friends")
def view_friends():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT friend.user1_id , friend.user2_id , friend.friendship_date , u1.username , u2.username 
            FROM friend
            JOIN user u1 ON friend.user1_id = u1.user_id
            JOIN user u2 ON friend.user2_id = u2.user_id
            WHERE friend.user1_id = 'u2';
        ''')
        friend = cur.fetchall()

    except mysql.connector.Error as e:
        # Error handling
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"
    
    finally:
        cur.close()
        conn.close()
        
    return render_template("friend/friend.html", friend=friend)

@friendlist_bp.route("/add-friend", methods=["GET", "POST"])
def add_friend():
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor()

            # Get the user and game from the form
            user1 = request.form["user"]
            user2 = request.form["friend"]
            date = datetime.datetime.today().strftime("%Y-%m-%d")

            # Check if user2 exists
            cur.execute('''
                SELECT user_id FROM user WHERE username = %s;
            ''', (user2,))

            result = cur.fetchone()

            if result:
                user2_id = result[0]  # Get the user_id of the friend

                # Insert a new entry into the friend table
                cur.execute('''
                    INSERT INTO friend (user1_id, user2_id, friendship_date)
                    VALUES (%s, %s, %s);
                ''', (user1, user2_id, date))  # Use user2_id, not friend_username

                # Commit the transaction
                conn.commit()
                return view_friends()
            
            else:
                return "Friend not found in the database"


        except mysql.connector.Error as e:
            # Error handling
            print(f"Error: {e}")
            return f"Error Addding Friend {e}"
        
        finally:
            cur.close()
            conn.close()

    return render_template("friend/add_friend.html")

'''@friendlist_bp.route("/delete-friends")
def view_users():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(
            dictionary=True
        )  # Use `dictionary=True` to get results as dicts

        # Select all entries from the users table
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        return jsonify(users)

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"
    finally:
        cur.close()
        conn.close()'''