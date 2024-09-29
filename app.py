from flask import Flask, render_template, request, jsonify, Blueprint
import mysql.connector
import config

# import routes
from routes.users import user_bp
from routes.sample import sample_bp
from routes.review import review_bp
from routes.friend import friend_bp

app = Flask(__name__)

# add url route to all endpoints under /users
# ie. localhost:8000/users/...
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(sample_bp, url_prefix="/sample")
app.register_blueprint(review_bp, url_prefix="/review")
app.register_blueprint(friend_bp, url_prefix="/friend")


# routes == MAIN
@app.route("/")
def home():
    return render_template("main/home.html")


# == ALL GAMES ==
@app.route("/games")
def viewGames():
    return render_template("games/viewGames.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
