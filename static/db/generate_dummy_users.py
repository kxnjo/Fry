import random
import string
import hashlib
import sys
import os
from datetime import date
import mysql.connector

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
import os

load_dotenv('config.env')


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_DATABASE"),
    )


def getUserNum(cur):
    cur.execute("SELECT * from user;")
    return len(cur.fetchall())


def checkUser(cur, name, email):
    cur.execute(
        """
        SELECT * FROM user
        WHERE username = %s OR email = %s
    """,
        (name, email),
    )
    users = cur.fetchall()
    if len(users) != 0:
        print("Username or email is not unique! Please enter again.")
        return False

    print("No existing users with the same name and email! Proceed to create account.")
    return True


# Sample data for realistic names and email domains
first_names = [
    "John",
    "Jane",
    "Michael",
    "Emily",
    "Chris",
    "Sarah",
    "David",
    "Anna",
    "James",
    "Laura",
    "Daniel",
    "Megan",
    "Matthew",
    "Hannah",
    "Joshua",
    "Olivia",
    "Andrew",
    "Sophia",
    "Ryan",
    "Grace",
]
last_names = [
    "Smith",
    "Johnson",
    "Williams",
    "Jones",
    "Brown",
    "Davis",
    "Miller",
    "Wilson",
    "Moore",
    "Taylor",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Robinson",
]
email_providers = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com"]


def generate_username(first_name, last_name):
    """Generate a realistic username based on name and random numbers"""
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"


def generate_email(username):
    """Generate a realistic email based on username and a random email provider"""
    return f"{username}@{random.choice(email_providers)}"


def generate_random_password(length=12):
    """Generate a random password of fixed length"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


def generate_dummy_users(cur, conn, num_users=30):
    """
    Generate and insert a specified number of dummy users into the database.

    Parameters:
    ----------
    cur : mysql.connector.cursor
        The database cursor object used to execute SQL queries.
    conn : mysql.connector.connection
        The database connection object to commit changes.
    num_users : int
        The number of dummy users to generate.
    """
    for _ in range(num_users):
        # Generate unique dummy data
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = generate_username(first_name, last_name)
        email = generate_email(username)
        # password = generate_random_password()  # Generate a random password
        password = "password123"  # Generate a random password
        role = "user"
        created_on = date.today()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check if user or email already exists before insertion
        if checkUser(cur, username, email):
            # Generate a unique user_id
            uid = f"u{getUserNum(cur) + 1}"

            # Insert the dummy user into the database
            create_table_query = """
                INSERT INTO user (user_id, username, email, password, created_on, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            try:
                cur.execute(
                    create_table_query,
                    (uid, username, email, hashed_password, created_on, role),
                )
                print(f"Inserted user {uid}: {username}, {email} with password: {password}")
            except Exception as e:
                print(f"Failed to insert user {username}: {e}")

    # Commit all changes after insertion
    conn.commit()


if __name__ == "__main__":
    # Number of dummy users to generate
    NUM_USERS = 50

    # Connect to your database
    conn = create_connection()
    if conn is None:
        print("Failed to connect to database")
    else:
        try:
            cur = conn.cursor(dictionary=True)
            # Generate dummy users
            generate_dummy_users(cur, conn, num_users=NUM_USERS)

        except Exception as e:
            print(f"Error during dummy user generation: {e}")

        finally:
            # Close the cursor and connection
            if cur:
                cur.close()
            if conn:
                conn.close()
