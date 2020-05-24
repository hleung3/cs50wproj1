import os

from flask import Flask, Response, redirect, url_for, request, session, abort
from flask import redirect, render_template, request, session, jsonify, flash
from functools import wraps
from flask_session import Session
import random
import requests
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager,  UserMixin, login_required, login_user, logout_user
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__, instance_relative_config=False)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
print(os.getcwd())
sesh = Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(session)
        if not session.get("logged_in"):
            session.pop("username",None)
            session.pop("logged_in",None)
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# some protected url
@app.route('/')
@login_required
def index():
    return render_template("index.html")


# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    # session.remove()
    print(session)
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == 'POST':
        print("post")
        query = db.execute("SELECT * FROM \"Users\"" +
                            " where username = :username",
                            {"username":username}).fetchone()
        flash(str(query))
        ## fix this so that it works with users not in DB
        if query != None and password == query[2]:
            print(password,query[2])
            session['username'] = username
            session['logged_in'] = True
            session.modified = True
            return redirect("/")
        else:
            # I think it will be better to
            #  display an error message on login page
            # error in login go to error page
            return abort(401)
    else:
        return render_template("login.html")


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    ## TODO: make it so that it
    ## redirects to error page with a specific message
    return Response('<p>Login failed</p> <a href="/login">Login</a>')


## make a register page
@app.route("/register",methods=["GET","POST"])
def register():
    pass
@app.route("/search", methods=["GET"])
@login_required
def search():
    pass
@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):
    pass
