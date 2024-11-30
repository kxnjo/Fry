from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
import os
import importlib.util
import random
from datetime import datetime, timedelta

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


def generate_random_date():
    """
    Generates a random date and time within the current year.
    
    Returns:
        datetime: A `datetime` object representing the random date and time.
    """
    # Define the range for the current year
    current_year = datetime.now().year
    start_date = datetime(current_year, 1, 1)  # Start of the year
    end_date = datetime(current_year, 12, 31, 23, 59, 59)  # End of the year
    
    # Calculate the difference between start and end dates
    delta = end_date - start_date

    # Generate a random number of seconds within the range
    random_seconds = random.randint(0, int(delta.total_seconds()))

    # Return the random date
    return start_date + timedelta(seconds=random_seconds)



def update_created_on_field(db):
    """
    Updates the `created_on` field in the database.
    Converts the string `created_on` field to a `Date` object with a random date within the year.
    Args:
        db: The MongoDB database instance.
    """
    try:
        users = db.new_user.find({}, {"_id": 1, "created_on": 1})  # Fetch _id and created_on fields only
        updates = []

        for user in users:
            random_date = generate_random_date()
            updates.append(
                {
                    "filter": {"_id": user["_id"]},
                    "update": {"$set": {"created_on": random_date}}
                }
            )

        # Perform the bulk update
        if updates:
            result = db.new_user.bulk_write(
                [UpdateOne(update["filter"], update["update"]) for update in updates]
            )
            print(f"Updated {result.modified_count} user(s) with new `created_on` values.")
        else:
            print("No users found to update.")
    except Exception as e:
        print(f"Error updating `created_on` field: {e}")
        raise


# Main logic
if __name__ == "__main__":
    try:
        # Initialize the database
        db = initialize_database()

        # Update the `created_on` field
        # update_created_on_field(db)

        # Query users sorted by created_on (ascending)
        users = db.new_user.find().sort("created_on", -1)  # Change to -1 for descending order

        for user in users:
            print(user)

    except Exception as e:
        print(f"Unexpected error: {e}")
