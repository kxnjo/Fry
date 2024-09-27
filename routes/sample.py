from flask import Blueprint, jsonify
import mysql.connector
import config

# Create a Blueprint object
sample_bp = Blueprint("sample_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


@sample_bp.route("/create-table")
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


@sample_bp.route("/view-tables")
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
        conn.close()


@sample_bp.route("/view-users")
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
        conn.close()
