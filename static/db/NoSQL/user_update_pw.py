import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import importlib.util

# Load configurations from `config.env`
load_dotenv('config.env')

# MongoDB setup
mongo_cfg_path = "/Users/xinhui/Desktop/Y2T1/INF2003 Database Systems/Project/Fry-xh copy/mongo_cfg.py"

# Load the `mongo_cfg.py` dynamically
spec = importlib.util.spec_from_file_location("mongo_cfg", mongo_cfg_path)
mongo_cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mongo_cfg)

# Global database connection
db = None


def initialize_database():
    """Helper function to initialize the MongoDB connection."""
    global db
    if db is None:
        try:
            # Attempt to get an existing connection
            db = mongo_cfg.get_NoSQLdb()

            # If no existing connection, initialize a new one
            if db is None:
                app = {}  # Placeholder, update with your actual application object if required
                db = mongo_cfg.noSQL_init(app)

            if db is None:
                raise Exception("Failed to initialize MongoDB connection")
            print("Database successfully initialized.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    return db


def update_all_passwords(db, new_password):
    """
    Updates all user passwords in the database to a new bcrypt-hashed password.
py
    Args:
        db: The MongoDB database instance.
        new_password: The new plaintext password to assign to all users.
    """
    # if len(new_password) < 8:
    #     raise ValueError("New password must be at least 8 characters long for security reasons.")

    # Generate a bcrypt hash for the new password
    bcrypt_hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    try:
        # Perform the bulk update
        result = db.new_user.update_many(
            {},  # Matches all users in the collection
            {"$set": {"password": bcrypt_hashed_password}}
        )
        print(f"Updated {result.modified_count} user(s) with the new password.")
    except Exception as e:
        print(f"Error updating passwords: {e}")
        raise


# Main logic
if __name__ == "__main__":
    try:
        # Initialize the database
        db = initialize_database()

        # Set a new default password
        new_password = "pw123"  # Replace with your desired default password
        update_all_passwords(db, new_password)

    except ValueError as ve:
        print(f"Input error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")
