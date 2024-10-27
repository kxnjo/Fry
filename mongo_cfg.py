from pymongo import MongoClient
from flask import Flask

client = None
db = None


def noSQL_init(app: Flask):
    global client, db  # Declare global variables to modify them

    # Initialize MongoDB connection
    try:
        client = MongoClient("mongodb+srv://2301915:trytohackthisuf00l@fry-nosql.c1xaw.mongodb.net/?retryWrites=true&w=majority&appName=Fry-NoSQL")

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