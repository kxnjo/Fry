# ctrl F all the "lol" before pushing code 
from flask import Blueprint, render_template, request
import mysql.connector 
import config
import datetime
from auth_utils import login_required  # persistent login

# Create a Blueprint object
owned_game_bp_test = Blueprint("owned_game_bp_test", __name__)

# Connection to sql database 
def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

@owned_game_bp_test.route("/view-owned_game")
@login_required

def veiw_owned_game():
    conn = create_connection()
    if conn is None: 
        return "Failed to connect to database"
    try: 
        cur = conn.cursor() 
        
        get_table_query = """ 
            SELECT username, title, purchase_date, hours_played, owned_game.user_id, owned_game.game_id FROM owned_game
            INNER JOIN user ON owned_game.user_id = user.user_id
            INNER JOIN game ON owned_game.game_id = game.game_id;
        """
        cur.execute(get_table_query)
        owned_game = cur.fetchall()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving owned_game: {e}"
    finally: 
        cur.close() 
        conn.close()

    return render_template("owned_game/owned_game.html", owned_game = owned_game)

@owned_game_bp_test.route("/add-to-owned_game", methods=["GET", "POST"])
def addToOwned_game():
    if request.method == "POST":
        conn = create_connection()
        if conn is None: 
            return "Failed to connect to database"
        try:
            cur = conn.cursor(dictionary=True)
            user = request.form["user"] # what does this do lol
            game = request.form["game"]
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            hours = request.form["hours"] # i think this is wrong lol 
            
            print("this is the date:", date)
            
            # how to input the purchase date and hours played lol 
            # is it supposed to b %.2f for hours played lol
            insert_table_query = """
                INSERT INTO owned_game (user_id, game_id, purchase_date, hours_played) 
                VALUES (%s, %s, %s, %.2f)
            """
            
            # Execute the SQL statement
            cur.execute(
                insert_table_query,
                (user, game, date, hours),
            )
            conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            # Check if the error is a duplicate entry error (error code 1062)
            if e.errno == 1062:
                print("Duplicate entry error!")
                return f"Game is already in owned_game!"
            else:
                # For any other error, print the general error message
                print(f"Error: {e}")
                return f"Error adding to wanted_games: {e}"
        finally:
            cur.close()
            conn.close()

    return veiw_owned_game()

""" 
            SELECT 
                owned_game.user_id, 
                owned_game.game_id,
                owned_game.purchase_date,  
                owned_game.hours_played, 
                user.username, 
                game.title, 
            FROM 
                owned_game

            INNER JOIN user ON owned_game.user_id = user.user_id
            INNER JOIN game ON owned_game.game_id = game.game_id;
        """

