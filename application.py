# RUN BEFORE OPERATING FLASK:
# API_KEY=AIzaSyBBd2ui_STN7z6EyoawLpQ9oS8PZ-0stN8 (NO need to export, automaticly done below)
import time
import requests
import json
import random
import os
import re
from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session, Response, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from datetime import datetime


# define variables that will be used later
location = None
destination = None
arrivalTime = None

# Set API Key
key = "AIzaSyDMhsvLB5Sa0jizEcPExguTmTPLyDi_fNU"

# Configure applicxation
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Configure session to use filesystem (instead of signed cookies), inlcuding static files
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# ensures JS updates... https://stackoverflow.com/questions/41144565/flask-does-not-see-change-in-js-file
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
Session(app)

# set the secret key (instructions found on google "Flask Secret Key"):
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///walk.db")


@app.route("/")
def index():
    """Homepage"""

    # return index info
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # lowercase username
        username = request.form.get("username").lower()

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session["my_name"] = username

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Lowercase username
        username = request.form.get("username").lower()

        # Ensure username was submitted and ≠ users
        if not request.form.get("username") or username == "users":
            return apology("must provide new username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password again", 400)

        # Ensure terms are agreed to
        elif not request.form.get("terms"):
            return apology("must agree to Terms & Conditions", 400)

        # Ensure password = confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must provide matching passwords", 400)

        # Generate hash for password
        hash = generate_password_hash(request.form.get("password"))

        # Check to see if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)
        if len(rows) != 0:
            return apology("username already taken", 400)

        # Insert new user into database into master users list
        new_user_id = db.execute("INSERT INTO users (username, hash, first_name, last_name) VALUES (:username, :hash, :first, :last)",
                                 username=username, hash=hash, first=request.form.get("first").title(), last=request.form.get("last").title())

        # Query database for userid
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Forget any user_id
        session.clear()

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Account settings"""
    print(request.form)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # check to see if request is to change password
        if request.form['submission'] == "change":
            # Ensure password was submitted
            if not request.form.get("password"):
                return flash("You must provide a password")

            # Ensure confirmation was submitted
            elif not request.form.get("confirmation"):
                return flash("You must provide your password again")

            # Ensure password = confirmation
            elif request.form.get("password") != request.form.get("confirmation"):
                return flash("Passwords do not match")

            # Generate hash for password
            hash = generate_password_hash(request.form.get("password"))

            # update password in database
            update = db.execute("UPDATE users SET hash = :hash WHERE user_id = :id",
                                id=session["user_id"], hash=hash)
            if update:
                # Clear session and redirect user to login page
                session.clear()
                flash("Your password has been successfully changed!")
                return redirect("/")
            else:
                return apology("Error", 400)

        # check if attempting to delete account
        elif request.form['submission'] == "delete":
            # ensure confirmation box is checked
            if not request.form.get("deletecheck"):
                flash("Check the box below if you would like to delete your account.")
            # delete account (remove user from master users and remove usertable)
            else:
                # remove user from master users table
                delete = db.execute("DELETE FROM users WHERE user_id = :user",
                                    user=session["user_id"])
                # remove all rows that include user in friends
                friendslist = db.execute(
                    "DELETE FROM friends WHERE friend = :name OR user = :name", name=session["my_name"])

                # Forget any user_id
                session.clear()
                # Redirect to homepage
                return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("change.html")


@app.route("/map", methods=['POST', 'GET'])
@login_required
def map():
    """map"""

    # if post
    if request.method == "POST":
        # check to see refreshing
        if request.form['refresh'] == "refreshed":
            # return refreshed map
            return redirect("/map")
    else:
        # handle non key
        if not key:
            raise RuntimeError("API_KEY not set")
        return render_template("map.html", key=key)


@app.route("/friends", methods=["GET", "POST"])
@login_required
def friends():
    """friends"""
    # Query for list of friends
    friends = db.execute("SELECT friend FROM friends WHERE user = :name", name=session["my_name"])
    # initiate list of friends
    friendslist = list()
    # for each item in sql output, find which is friend and add to friendslist
    for row in friends:
        # query for all information from users about each, append to list to send to send to jinja/html in friends.html
        friend = db.execute(
            "SELECT username, destination, dep_time, location FROM users WHERE username = :name", name=row["friend"])
        friendslist.append(friend[0])

    # collect current_request
    current = db.execute(
        "SELECT destination, dep_time, location FROM users WHERE user_id = :id", id=session["user_id"])
    session["current_request"] = current[0]

    # User reached route via POST (as by submitting a form via GET)
    if request.method == "POST":
        # Ensure username was submitted /exists
        # query sequel
        newfriend = db.execute("SELECT * FROM users WHERE username = :username",
                               username=request.form.get("newfriend").lower())
        if not request.form.get("newfriend"):
            flash("You must provide a username to add!")
        elif len(newfriend) != 1:
            flash("Username does not exist!")
        elif newfriend[0]["user_id"] == session["user_id"]:
            flash("You cannot add yourself!")
        else:
            # check to see if you are on their list
            check = db.execute("SELECT * FROM friends WHERE user = :friend_name AND friend = :my_name",
                               friend_name=request.form.get("newfriend").lower(), my_name=session["my_name"])
            if len(check) != 0:
                newusername = request.form.get("newfriend").lower()
                flash(f"You're already friends with {newusername}!")
            else:
                # add to list
                addfriend = db.execute("INSERT INTO friends (friend, user) VALUES (:friend, :username)",
                                       friend=request.form.get("newfriend").lower(), username=session["my_name"])
                if not addfriend:
                    flash(f"You've already added {request.form.get('newfriend').lower()}!")

        # redirect to friends
        return redirect("/friends")
    # return friends template
    return render_template("friends.html", friends=friendslist)


# handle errors
def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


@app.route("/matches")
def matches():
    """Look up friend matches"""
    # query database for user info
    info = db.execute(
        "SELECT destination, dep_time FROM users WHERE username = :user", user=session["my_name"])

    # select list of all friends headed to the same place at the same time
    friends = db.execute("SELECT location, dep_time FROM users JOIN friends ON friends.user = users.username WHERE friends.friend = :user AND users.destination = :destination AND users.dep_time = :time",
                         user=session["my_name"], destination=info[0]["destination"], time=info[0]["dep_time"])

    # return jsonifyed info
    return jsonify(friends)


@app.route("/position")
def position():
    """Look up friend matches"""

    # query for user's current position
    info = db.execute(
        "SELECT location, destination FROM users WHERE username = :user", user=session["my_name"])

    # return jsonifyed info
    return jsonify(info)


@app.route("/request", methods=["GET", "POST"])
@login_required
def order():
    """request"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # if submission is a new request
        if request.form['submission'] == "request":
            # ensure location is given
            if not request.form.get("location"):
                flash("You must provide your current location!")
            # ensure destination is given
            elif not request.form.get("destination"):
                flash("You must provide a destination!")
            # ensure time is given
            elif not request.form.get("arrival"):
                flash("You must provide an arrival time!")
            # if all is given
            else:
                # update database with new request
                update = db.execute("UPDATE users SET destination = :destination, dep_time = :arrival, location = :location WHERE user_id = :id",
                                    id=session["user_id"], destination=request.form.get("destination"), arrival=request.form.get("arrival"), location=request.form.get("location"))
                # redirect to map
                return redirect("/map")
            # redirect to request
            return redirect("/request")

        # if submission is to clear
        if request.form['submission'] == "clear":
            # clear database
            update = db.execute(
                "UPDATE users SET destination = NULL, location = NULL, dep_time = NULL WHERE user_id = :id", id=session["user_id"])
            # redirect to request
            return redirect("/request")

    # if get request
    else:
        # query database for current request
        select = db.execute(
            "SELECT destination, location, dep_time FROM users WHERE user_id = :id", id=session["user_id"])
        destination = select[0]['destination']
        arrival = select[0]['dep_time']
        location = select[0]['location']
        # return current request to request.html
        return render_template("request.html", destination=destination, arrival=arrival, location=location)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)