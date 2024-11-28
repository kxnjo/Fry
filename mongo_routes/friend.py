from flask import app, Blueprint, jsonify, render_template, request, url_for, redirect, session, flash
import mysql.connector
import pymongo

# images import
from bson.binary import Binary
import base64

# load up configurations
from dotenv import load_dotenv
import os
load_dotenv('config.env')

import hashlib
import json
import datetime
from auth_utils import login_required  # persistent login

# MongoDB setup
import mongo_cfg

# Create a Blueprint object
friendlist_bp = Blueprint("friendlist_bp", __name__)

db = None

def initialize_database():
    """Helper function to initialize the MongoDB user collection."""
    global db
    if db is None:
        # Attempt to get an existing connection first
        db = mongo_cfg.get_NoSQLdb()
        
        # If no existing connection, initialize a new one
        if db is None:
            db = mongo_cfg.noSQL_init(app)
        
        return db
            
    # After ensuring db is initialized, return the user collection if db is available
    if db is not None:
        return db
    else:
        raise Exception("Failed to initialize MongoDB connection")
    
@friendlist_bp.route("/view-friends")
@login_required
# Function to view friends
def view_friends():
    db = initialize_database()  
    if db is None:
        return "Database not initialized!!", 500
    
    documents = db.new_user.find()