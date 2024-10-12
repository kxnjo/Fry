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

        get_table_query = """
            SELECT 
                g.title, 
                wg.added_date, 
                wg.game_id,
                GROUP_CONCAT(DISTINCT d.developer_name SEPARATOR ', ') AS developer_name,
                GROUP_CONCAT(DISTINCT c.category_name SEPARATOR ', ') AS categories 
            FROM wanted_game wg
            INNER JOIN game g ON wg.game_id = g.game_id
            INNER JOIN game_developer gd ON wg.game_id = gd.game_id
            INNER JOIN developer d ON gd.developer_id = d.developer_id
            INNER JOIN game_category gc ON wg.game_id = gc.game_id
            INNER JOIN category c ON gc.category_id = c.category_id
            WHERE wg.user_id = %s
            GROUP BY g.title, wg.game_id;
        """
        
        cur.execute(
            get_table_query,
            (session['user_id'],)
            )
        
        wishlist = cur.fetchall()
        
        print(wishlist)
        
        gameRecommendation = recommendGame(session['user_id'])

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving wanted_games: {e}"
    finally:
        cur.close()
        conn.close()
    
    return render_template("wishlist/wishlist.html", wishlist=wishlist, search = False, gameRecommendation=gameRecommendation)

def recommendGame(user_id):
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
        
        recommendation_query = """
            SELECT 
                g.title,
                g.game_id,
                GROUP_CONCAT(DISTINCT d.developer_name SEPARATOR ', ') AS developer_name,
                GROUP_CONCAT(DISTINCT c.category_name SEPARATOR ', ') AS categories 
            FROM game g
            INNER JOIN game_developer gd ON g.game_id = gd.game_id
            INNER JOIN developer d ON gd.developer_id = d.developer_id
            INNER JOIN game_category gc ON g.game_id = gc.game_id
            INNER JOIN category c ON gc.category_id = c.category_id
            WHERE c.category_name IN (  SELECT DISTINCT c.category_name
                                        FROM wanted_game wg
                                        INNER JOIN game_category gc ON wg.game_id = gc.game_id
                                        INNER JOIN category c ON gc.category_id = c.category_id
                                        WHERE wg.user_id = '{}')
            AND g.game_id NOT IN (  SELECT wg.game_id
                                    FROM wanted_game wg
                                    WHERE wg.user_id = '{}')
            GROUP BY g.game_id
            ORDER BY RAND()
            LIMIT 6; 
        """.format(user_id, user_id)
        
        cur.execute(recommendation_query)
        
        recommendation = cur.fetchall()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving wanted_games: {e}"
    finally:
        cur.close()
        conn.close()
    
    return recommendation

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


@wishlist_bp.route("/delete-from-wishlist/<game_id>", methods=["GET"])
def deleteFromWishlist(game_id):
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor(dictionary=True)
        
        user_id = session['user_id']

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

@wishlist_bp.route("/search-wishlist", methods=["GET", "POST"])
def searchWishlist():
    if request.method == "POST":
        conn = create_connection()
        if conn is None:
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)
            
            string = request.form["searchInput"]
            
            search_table_query1 = """
                SELECT 
                    g.title, 
                    GROUP_CONCAT(DISTINCT d.developer_name SEPARATOR ', ') AS developer_name,
                    GROUP_CONCAT(DISTINCT c.category_name SEPARATOR ', ') AS categories, 
                    wg.game_id,
                    wg.added_date
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
                        (g.title LIKE "%{}%" OR d.developer_name LIKE "%{}%" OR c.category_name LIKE "%{}%")
                    )
                GROUP BY 
                    g.title, wg.game_id;
            """.format(session['user_id'], string, string, string)
            
            # Execute the SQL statement
            cur.execute(search_table_query1)
            
            searchResult = cur.fetchall()
            
            if (searchResult == []):
                search_table_query2 = """
                    SELECT 
                        g.title, 
                        GROUP_CONCAT(DISTINCT d.developer_name SEPARATOR ', ') AS developer_name,
                        GROUP_CONCAT(DISTINCT c.category_name SEPARATOR ', ') AS categories, 
                        wg.game_id,
                        wg.added_date
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
                    search_table_query2 += """
                        (g.title LIKE "%{}%" OR d.developer_name LIKE "%{}%" OR c.category_name LIKE "%{}%")
                        """.format(i, i, i)
                    count -= 1
                    if count != 0:
                        search_table_query2 += "OR"
                
                search_table_query2 += """
                        )
                    GROUP BY 
                        g.title, wg.game_id;
                    """

                # Execute the SQL statement
                cur.execute(search_table_query2)
                
                searchResult = cur.fetchall()

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Error: {e}")
            return f"Error searching from wanted_games: {e}"
        finally:
            cur.close()
            conn.close()

    return render_template("wishlist/wishlist.html", search=True, searchResult=searchResult, string=string)