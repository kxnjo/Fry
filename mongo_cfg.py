from pymongo import MongoClient
from flask import Flask

from dotenv import load_dotenv
import os

load_dotenv('config.env')

client = None
db = None

username = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
app_name = os.environ.get("MONGO_APP_NAME")


def noSQL_init(app: Flask):
    global client, db  # Declare global variables to modify them

    # Initialize MongoDB connection
    try:
        client = MongoClient(f"mongodb+srv://{username}:{password}@fry-nosql.c1xaw.mongodb.net/?retryWrites=true&w=majority&appName={app_name}")

        db = client.get_database("Fry-NoSQL")  # Make sure this matches your database name

        print("MongoDB connection established.")
        print("Collections:", db.list_collection_names())  # Check available collections
    except Exception as e:
        print("Failed to connect to MongoDB:", e)


# Optionally, you can create a function to return the db variable
def get_NoSQLdb():
    return db


## NOTE FOR ALL:
# In your individual routes , 'from mongo_cfg import noSQL_init()' to get access to mongoDB instance