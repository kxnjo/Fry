from flask import Flask, render_template, request

app = Flask(__name__)

# routes == MAIN
@app.route('/')
def home():
    return "hello world"

# == USER ROUTES ==
@app.route('/login')
def login():
    return render_template("user/login.html")

# == ALL GAMES == 
@app.route('/games')
def viewGames():
    return render_template("games/viewGames.html")

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 8000, debug = True)
