from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 3306
USER = "FryGames"
PASSWORD = "FryIsBetter"
DATABASE = "FryGames"

# database connections ==
def create_connection():
    try: 
        conn = mysql.connector.connect(
            host = HOST,
            port = PORT,
            user = USER,
            password = PASSWORD,
            database = DATABASE
        )
        print(conn)
        print(f"Connection Successful!")
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        return None;

@app.route("/create-table")
def create_table():
    conn = create_connection()
    if conn is None:
        return "Failed to connect to database"
    try:
        cur = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        # Execute the SQL statement
        cur.execute(create_table_query)
        conn.commit()  # Commit the transaction
        return "Table 'users' created successfully."
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return f"Error creating table: {e}"
    finally:
        cur.close()
        conn.close()

# routes == MAIN
@app.route("/")
def home():
    return render_template("main/home.html")

# == USER ROUTES ==
@app.route("/login")
def login():
    return render_template("user/login.html")


# == ALL GAMES ==
@app.route("/games")
def viewGames():
    return render_template("games/viewGames.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
