from flask import Blueprint, render_template, request, session
import mysql.connector
import config
import datetime
from auth_utils import login_required  # persistent login

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
@login_required
# Function to view friends
def view_friends():
    # Create a connection to the database
    conn = create_connection()
    user_id=session["user_id"] # Get the user_id from the session
    if conn is None:
        return "Failed to connect to database" # Return an error message if connection fails
    try:
        cur = conn.cursor()
        # Query to retrieve friends names and friendship date, and games they own and in wishlist
        cur.execute('''
            SELECT 
                f.user1_id, f.user2_id, f.friendship_date, u1.username, u2.username,
                IF(f.user1_id = %s,
                    GROUP_CONCAT(DISTINCT g2_wanted.title ORDER BY g2_wanted.title ASC),
                    GROUP_CONCAT(DISTINCT g1_wanted.title ORDER BY g1_wanted.title ASC)
                ) AS wanted_games,
                IF(f.user1_id = %s,
                    GROUP_CONCAT(DISTINCT g2_owned.title ORDER BY g2_owned.title ASC),
                    GROUP_CONCAT(DISTINCT g1_owned.title ORDER BY g1_owned.title ASC)
                ) AS owned_games
            FROM friend f
            JOIN user u1 ON f.user1_id = u1.user_id
            JOIN user u2 ON f.user2_id = u2.user_id
            LEFT JOIN wanted_game w1 ON f.user1_id = w1.user_id
            LEFT JOIN game g1_wanted ON w1.game_id = g1_wanted.game_id
            LEFT JOIN wanted_game w2 ON f.user2_id = w2.user_id
            LEFT JOIN game g2_wanted ON w2.game_id = g2_wanted.game_id
            LEFT JOIN owned_game o1 ON f.user1_id = o1.user_id
            LEFT JOIN game g1_owned ON o1.game_id = g1_owned.game_id
            LEFT JOIN owned_game o2 ON f.user2_id = o2.user_id
            LEFT JOIN game g2_owned ON o2.game_id = g2_owned.game_id
            WHERE f.user1_id = %s OR f.user2_id = %s
            GROUP BY f.user1_id, f.user2_id, f.friendship_date, u1.username, u2.username
        ''', (user_id, user_id, user_id, user_id))
        friends = cur.fetchall() # Get all friends

        friend_list = []
        for friend in friends:
            # Get the friend's user_id, username, friendship_date, owned_games, and wanted_games
            if friend[0] == user_id:
                friend_list.append((friend[1], friend[2], friend[4], friend[5], friend[6]))
            else:
                friend_list.append((friend[0], friend[2], friend[3], friend[5], friend[6]))


        # Get mutual friends
        mutual_friends = []
        for friend in friend_list:
            friend_id = friend[0] # Get the friend's user_id
            # Query to get mutual friends
            cur.execute('''
                SELECT DISTINCT u.user_id, u.username
                FROM friend mf
                JOIN user u ON
                    (u.user_id = mf.user1_id OR u.user_id = mf.user2_id)
                WHERE (
                    (mf.user1_id = %s AND EXISTS (
                        SELECT 1 FROM friend WHERE user1_id = %s AND user2_id = mf.user2_id
                    )) OR
                    (mf.user2_id = %s AND EXISTS (
                        SELECT 1 FROM friend WHERE user2_id = %s AND user1_id = mf.user1_id
                    ))) 
                    AND u.user_id NOT IN (%s, %s)
            ''', (user_id, friend_id, user_id, friend_id, user_id, friend_id))

            # Get all mutual friends for each friend in the friend list
            mutual_friends.append(cur.fetchall())
            
    except mysql.connector.Error as e:
        # Error handling
        conn.rollback()
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"
    
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()
        
    return render_template("friend/friend.html", friend_data=zip(friend_list, mutual_friends))


@friendlist_bp.route("/add-friend", methods=["GET", "POST"])
# Function to add a friend
def add_friend():
    # Create a connection to the database
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database" # Return an error message if connection fails

    try:
        cur = conn.cursor()
        # Get the user_id from the session
        user1 = session["user_id"]

        suggested_friends = []
        # Query to give friends suggestions
        cur.execute('''
            SELECT u.user_id, u.username
            FROM user u
            WHERE u.user_id != %s
            AND NOT EXISTS (
                SELECT 1
                FROM friend f
                WHERE (f.user1_id = u.user_id AND f.user2_id = %s)
                OR (f.user2_id = u.user_id AND f.user1_id = %s))
            ORDER BY RAND()
            LIMIT 4
        ''', (user1, user1, user1))

        suggested_friends = cur.fetchall() # Get all suggested friends

        # Check if the form was submitted (POST request), selected from suggestions or searched by username
        if request.method == "POST":
            # Check if a friend was selected from suggestions
            friend_id = request.form.get("friend_id")
            date = datetime.datetime.today().strftime("%Y-%m-%d")

            if friend_id:
                # Check if they're already friends
                cur.execute('''
                    SELECT * FROM friend 
                    WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
                ''', (user1, friend_id, friend_id, user1))
                
                if cur.fetchone():
                    error_message = "You are already friends with this user." # Return an error message if they're already friends
                    return render_template("friend/add_friend.html", suggested_friends=suggested_friends, error=error_message)

                # Insert a new entry into the friend table
                cur.execute('''
                    INSERT INTO friend (user1_id, user2_id, friendship_date)
                    VALUES (%s, %s, %s)
                ''', (user1, friend_id, date))

                conn.commit() # Commit the changes into the database
                return view_friends()  # Redirect to view friends after adding

            # For adding friends through username search
            user2 = request.form.get("friend")

            # Check if user2 exists
            cur.execute('SELECT user_id FROM user WHERE username = %s;', (user2,))
            result = cur.fetchone()

            if result:
                user2_id = result[0]  # Get the user_id of the friend

                # Check if they're already friends
                cur.execute('''
                    SELECT * FROM friend 
                    WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
                ''', (user1, user2_id, user2_id, user1))
                
                if cur.fetchone():
                    error_message = "You are already friends with this user." # Return an error message if they're already friends
                    return render_template("friend/add_friend.html", suggested_friends=suggested_friends, error=error_message)

                # Insert a new entry into the friend table
                cur.execute('''
                    INSERT INTO friend (user1_id, user2_id, friendship_date)
                    VALUES (%s, %s, %s)
                ''', (user1, user2_id, date))

                conn.commit() # Commit the changes into the database
                return view_friends() # Redirect to view friends after adding
            else:
                error_message = "Friend not found" # Return an error message if the friend is not found
                return render_template("friend/add_friend.html", suggested_friends=suggested_friends, error=error_message)


    except mysql.connector.Error as e:
        # Error handling
        conn.rollback()
        print(f"Error: {e}")
        return f"Error: {e}"
    
    finally:
        cur.close()
        conn.close()

    return render_template("friend/add_friend.html", suggested_friends=suggested_friends)

@friendlist_bp.route("/delete-friends/<user1_id>/<user2_id>")
# Function to delete a friend
def delete_friend(user1_id, user2_id):
    # Create a connection to the database
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database" # Return an error message if connection fails
    try:
        cur = conn.cursor(dictionary=True)

        # Query to delete a friend
        cur.execute("""
            DELETE FROM friend
            WHERE user1_id = %s AND user2_id = %s OR user1_id = %s AND user2_id = %s;
        """,(user1_id, user2_id, user2_id, user1_id))

        conn.commit() # Commit the changes into the database

    except mysql.connector.Error as e:
        # Error handling
        conn.rollback()
        print(f"Error: {e}")
        return f"Error deleting friend: {e}"
    finally:
        cur.close()
        conn.close()

    return view_friends() # Redirect to view friends after deleting

# Function to get mutual friends for the user dashboard
def get_dashboard_mutual_friends(user_id, friend_id):
    # Create a connection to the database
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database" # Return an error message if connection fails
    try:
        cur = conn.cursor()
        # Query to get mutual friends
        cur.execute('''
            SELECT DISTINCT u.user_id, u.username
            FROM friend mf
            JOIN user u ON
                (u.user_id = mf.user1_id OR u.user_id = mf.user2_id)
            WHERE (
                (mf.user1_id = %s AND EXISTS (
                    SELECT 1 FROM friend WHERE user1_id = %s AND user2_id = mf.user2_id
                )) OR
                (mf.user2_id = %s AND EXISTS (
                    SELECT 1 FROM friend WHERE user2_id = %s AND user1_id = mf.user1_id
                ))) 
                AND u.user_id NOT IN (%s, %s)
        ''', (user_id, friend_id, user_id, friend_id, user_id, friend_id))

        # Get all mutual friends for each friend in the friend list
        friends = cur.fetchall()

    except mysql.connector.Error as e:
        # Error handling
        conn.rollback()
        print(f"Error: {e}")
        return f"Error deleting friend: {e}"
    finally:
        cur.close()
        conn.close()

    return friends # Return the mutual friends