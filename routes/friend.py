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
def view_friends():
    conn = create_connection()
    user_id=session["user_id"]
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
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
            GROUP BY f.user1_id, f.user2_id, f.friendship_date, u1.username, u2.username;
        ''', (user_id, user_id, user_id, user_id))
        friends = cur.fetchall()

        friend_list = []
        for friend in friends:
            if friend[0] == user_id:
                friend_list.append((friend[0], friend[1], friend[2], friend[4], friend[5], friend[6]))
            else:
                friend_list.append((friend[1], friend[0], friend[2], friend[3], friend[5], friend[6]))


        # Get mutual friends
        mutual_friends = []
        for friend in friend_list:
            friend_id = friend[1]  # user2_id
            cur.execute('''
                SELECT DISTINCT u.user_id, u.username
                FROM friend mf
                JOIN user u ON 
                    (u.user_id = mf.user1_id OR u.user_id = mf.user2_id)
                WHERE (
                    (mf.user1_id = %s AND mf.user2_id IN (
                        SELECT user2_id FROM friend WHERE user1_id = %s
                    )) OR
                    (mf.user2_id = %s AND mf.user1_id IN (
                        SELECT user1_id FROM friend WHERE user2_id = %s
                    ))
                ) AND u.user_id NOT IN (%s, %s)
            ''', (user_id, friend_id, user_id, friend_id, user_id, friend_id))

            # Get all mutual friends for each friend in the friend list
            mutual_friends.append(cur.fetchall())  
            
    except mysql.connector.Error as e:
        # Error handling
        conn.rollback()
        print(f"Error: {e}")
        return f"Error retrieving users: {e}"
    
    finally:
        cur.close()
        conn.close()
        
    return render_template("friend/friend.html", friend_data=zip(friend_list, mutual_friends))


@friendlist_bp.route("/add-friend", methods=["GET", "POST"])
def add_friend():
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor()

            # Get the user and friend from the form
            user1 = session["user_id"]
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
            conn.rollback()
            print(f"Error: {e}")
            return f"Error Addding Friend {e}"
        
        finally:
            cur.close()
            conn.close()

    return render_template("friend/add_friend.html")

@friendlist_bp.route("/delete-friends/<user1_id>/<user2_id>", methods=["POST"])
def delete_friend(user1_id, user2_id):
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)

        # Execute the SQL statement
        cur.execute("""
            DELETE FROM friend
            WHERE user1_id = %s AND user2_id = %s OR user1_id = %s AND user2_id = %s;
        """,(user1_id, user2_id, user2_id, user1_id))

        conn.commit()

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error: {e}")
        return f"Error deleting friend: {e}"
    finally:
        cur.close()
        conn.close()

    return view_friends()