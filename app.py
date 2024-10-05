from flask import Flask, render_template, request, jsonify, Blueprint, session
import config

# import routes
from routes.users import user_bp
from routes.game import game_bp
from routes.sample import sample_bp
from routes.review import review_bp
from routes.category import category_bp
from routes.developer import developer_bp
from routes.friend import friendlist_bp
from routes.wishlist import wishlist_bp
from routes.owned_game import owned_game_bp

app = Flask(__name__)
app.secret_key = "ifreakinghatethistrimester"  # for session security

# add url route to all endpoints under /users
# ie. localhost:8000/users/...
app.register_blueprint(user_bp, url_prefix="/user")
app.register_blueprint(game_bp, url_prefix="/game")
app.register_blueprint(sample_bp, url_prefix="/sample")
app.register_blueprint(review_bp, url_prefix="/review")
app.register_blueprint(category_bp, url_prefix="/category")
app.register_blueprint(developer_bp, url_prefix="/developer")
app.register_blueprint(friendlist_bp, url_prefix="/friendlist")
app.register_blueprint(wishlist_bp, url_prefix="/wishlist")
app.register_blueprint(owned_game_bp, url_prefix="/owned_game")


# routes == MAIN
@app.route("/")
def home():
    print(session)
    return render_template("main/home_old.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
