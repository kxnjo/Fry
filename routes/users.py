from flask import Blueprint, jsonify
import mysql.connector
import config

# Create a Blueprint object
users_bp = Blueprint("users_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


# == USER ROUTES ==
@users_bp.route("/login")
def login():
    return render_template("user/login.html")
