from flask import Blueprint, render_template, request, session, redirect, url_for
import mysql.connector
import config
from auth_utils import login_required  # persistent login
import random, datetime

# Create a Blueprint object
owned_game_bp = Blueprint("owned_game_bp", __name__)

# Create connection to sql 
def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )

#view owned_game
@owned_game_bp.route("/view-owned_game")
@login_required
def view_owned_game():
    conn = create_connection()
    if conn is None: 
        return "Failed to connect to database"
    try: 
        cur = conn.cursor() 
        
        # view games that the user owns 
        cur.execute(""" 
            SELECT 
                game.title,
                owned_game.user_id, 
                owned_game.game_id,
                owned_game.purchase_date,  
                owned_game.hours_played
            FROM 
                owned_game

            INNER JOIN game ON owned_game.game_id = game.game_id
            WHERE owned_game.user_id = %s ;
        """, (session['user_id'],))

        # Fetch owned_games rows
        owned_game = cur.fetchall()

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error retrieving owned_game: {e}"
    finally: 
        cur.close() 
        conn.close()

    return render_template("owned_game/owned_game.html", owned_game = owned_game)

# insert owned_game
@owned_game_bp.route("/add-owned_game", methods=["GET", "POST"])
def add_owned_game():
    if request.method == "POST":
        conn = create_connection()
        if conn is None: 
            return "Failed to connect to database"
        try: 
            cur = conn.cursor() 
            
            # retrieve selected game? lol
            # selected_gameID = request.args.get('game')
            game = request.form["game"]
            date = datetime.datetime.today().strftime("%Y-%m-%d")
            hours = 0

            # add games that the user owns 
            cur.execute(""" 
                INSERT INTO owned_game( 
                    user_id, 
                    game_id,
                    purchase_date,
                    hours_played)
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], game, date, hours))
            print(f"{game} Saved to Owned Games")
            
            conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            # Check if the error is a duplicate entry error (error code 1062)
            if e.errno == 1062:
                print("Duplicate entry error!")
                return f"NOOOO! Game is already in Owned Games!"
            else:
                print(f"Error: {e}")
                return f"Error retrieving owned_game: {e}"
        finally: 
            cur.close() 
            conn.close()

    return view_owned_game() 
