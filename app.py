from flask import Flask, render_template, request, jsonify, Blueprint, session
from datetime import timedelta

# MongoDB
from dotenv import load_dotenv
import os
load_dotenv('config.env')
from mongo_cfg import noSQL_init

# import routes
from mongo_routes.users import user_bp
from mongo_routes.wishlist import wishlist_bp
from mongo_routes.owned_game import owned_game_bp
from mongo_routes.friend import friendlist_bp
from mongo_routes.game import game_bp
from mongo_routes.category import category_bp
from mongo_routes.developer import developer_bp
from mongo_routes.review import review_bp

app = Flask(__name__)
noSQL_init(app)
app.secret_key = "INF2003DatabaseProject"  # for session security

# Set the permanent session lifetime globally
app.permanent_session_lifetime = timedelta(days=31)

@app.before_request
def make_session_permanent():
    session.permanent = True  # Make the session permanent on every request

# add url route to all endpoints under /users
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(game_bp, url_prefix="/game")
app.register_blueprint(review_bp, url_prefix="/review")
app.register_blueprint(category_bp, url_prefix="/category")
app.register_blueprint(developer_bp, url_prefix="/developer")
app.register_blueprint(friendlist_bp, url_prefix="/friendlist")
app.register_blueprint(wishlist_bp, url_prefix="/wishlist")
app.register_blueprint(owned_game_bp, url_prefix="/owned_game")


# routes == MAIN
@app.route("/")
def home():
    print(f"session: {session}")
    return render_template("main/home.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
