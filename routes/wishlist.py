from flask import Blueprint, render_template, request
import mysql.connector
import config
import datetime

# Create a Blueprint object
wishlist_bp = Blueprint("wishlist_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


@wishlist_bp.route("/view-wishlist")
def view_wishlist():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()

        cur.execute("SELECT * FROM wanted_game")
        wishlist = cur.fetchall()
        
        for i in wishlist:
            print(i[0])
            print(i[1])
            print(i[2])

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving wanted_games: {e}"
    finally:
        cur.close()
        conn.close()
    
    return render_template("wishlist/wishlist.html", wishlist=wishlist)

@wishlist_bp.route("/add-to-wishlist", methods=["GET", "POST"])
def addToWishlist():
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)

            user = request.form["user"]
            game = request.form["game"]
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            
            print("this is the date:", date)
            
            insert_table_query = """
                INSERT INTO wanted_game (user_id, game_id, added_date) 
                VALUES (%s, %s, %s)
            """

            # Execute the SQL statement
            cur.execute(
                insert_table_query,
                (user, game, date),
            )
            conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error adding to wishlist: {e}"
        finally:
            cur.close()
            conn.close()

    return view_wishlist()

@wishlist_bp.route("/delete-from-wishlist/<user_id>/<game_id>", methods=["GET"])
def deleteFromWishlist(user_id, game_id):
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        
        print("this is the user:", user_id)
        print("this is the game:", game_id)

        
        delete_table_query = """
            DELETE FROM wanted_game
            WHERE user_id = %s AND game_id = %s
        """

        # Execute the SQL statement
        cur.execute(
            delete_table_query,
            (user_id, game_id),
        )
        conn.commit()

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error: {e}")
        return f"Error deleting from wishlist: {e}"
    finally:
        cur.close()
        conn.close()

    return view_wishlist()