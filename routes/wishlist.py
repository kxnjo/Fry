from flask import Blueprint, render_template, request, session
import mysql.connector # type: ignore
import config
import datetime
from auth_utils import login_required  # persistent login

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
@login_required
def view_wishlist():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
        
        print(session['user_id'])

        get_table_query = """
            SELECT username, title, added_date, wanted_game.user_id, wanted_game.game_id FROM wanted_game
            INNER JOIN user ON wanted_game.user_id = user.user_id
            INNER JOIN game ON wanted_game.game_id = game.game_id
            WHERE user.user_id = %s;
        """
        
        cur.execute(
            get_table_query,
            (session['user_id'],)
            )
        
        wishlist = cur.fetchall()

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

            user = session['user_id']
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
            # Check if the error is a duplicate entry error (error code 1062)
            if e.errno == 1062:
                print("Duplicate entry error!")
                return f"NOOOO! Game is already in wishlist!"
            else:
                # For any other error, print the general error message
                print(f"Error: {e}")
                return f"Error adding to wanted_games: {e}"
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
        return f"Error deleting from wanted_games: {e}"
    finally:
        cur.close()
        conn.close()

    return view_wishlist()

@wishlist_bp.route("/search-wishlist")
def searchWishlist():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        
        string = "City Medal"

        search_table_query = """
            SELECT 
                g.title, 
                g.price, 
                d.developer_name, 
                GROUP_CONCAT(DISTINCT c.category_name SEPARATOR ', ') AS categories, 
                wg.game_id
            FROM 
                wanted_game wg
            INNER JOIN 
                game g ON wg.game_id = g.game_id
            INNER JOIN 
                game_developer gd ON wg.game_id = gd.game_id
            INNER JOIN 
                developer d ON gd.developer_id = d.developer_id
            INNER JOIN 
                game_category gc ON wg.game_id = gc.game_id
            INNER JOIN 
                category c ON gc.category_id = c.category_id
            WHERE 
                wg.user_id = '{}'
            AND 
                (
        """.format(session['user_id'])
        
        count = len(string.split())
        for i in string.split():
            search_table_query += """
                (g.title LIKE '%{}%' OR d.developer_name LIKE '%{}%' OR c.category_name LIKE '%{}%')
                """.format(i, i, i)
            count -= 1
            if count != 0:
                search_table_query += "OR"
        
        search_table_query += """
                )
            GROUP BY 
                g.title, g.price, d.developer_name, wg.game_id
            ORDER BY 
                g.title ASC;
            """
        
        print(search_table_query)

        # Execute the SQL statement
        cur.execute(search_table_query)
        
        searchResult = cur.fetchall()
        print("RESULT:")
        print(searchResult)

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Error: {e}")
        return f"Error searching from wanted_games: {e}"
    finally:
        cur.close()
        conn.close()

    return render_template("wishlist/wishlist.html", searchResult=searchResult)