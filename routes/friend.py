from flask import Blueprint, jsonify, render_template
import mysql.connector
import config

# Create a Blueprint object
friend_bp = Blueprint("friend_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

'''@friend_bp.route("/view-tables")
def view_tables():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()

        # Step 1: Get all table names
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()

        table_details = {}

        # Step 2: Get schema details for each table
        for (table_name,) in tables:
            cur.execute(f"DESCRIBE {table_name}")
            table_details[table_name] = cur.fetchall()

        return jsonify(table_details)

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving tables: {e}"
    finally:
        cur.close()
        conn.close()'''


'''@friend_bp.route("/view-users")
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

@friend_bp.route("/update-friends")
def updatefriends():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT friend.user1_id AS u1, friend.user2_id AS u2, friend.friendship_date AS date,
                    u1.username AS username1, u2.username AS username2
            FROM friend
            JOIN user u1 ON friend.user1_id = u1.user_id
            JOIN user u2 ON friend.user2_id = u2.user_id
            WHERE friend.user1_id = 'u2';
        ''')
        rows = cur.fetchall()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"
    
    # Create a list to hold review data
    friend = []
    if rows:
        for row in rows:
            friend_data = {
                "user1_id": row[0],
                "user2_id": row[1],
                "friendship_date": row[2],
                "username1": row[3],
                "username2": row[4]
            }
            friend.append(friend_data)
    else:
        print("not found")

    return render_template("friend/friend.html", friend=friend)

    #finally:
        #cur.close()
        #conn.close()

'''@friend_bp.route("/filter-friendlist")
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

'''@friend_bp.route("/add-friend")
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

'''@friend_bp.route("/delete-friends")
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