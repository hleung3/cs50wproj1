import os

from flask import Flask, Response, redirect, url_for, request, session, abort
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
# app.config["SECRET_KEY"] = "secret1"
# app.config["DEBUG"] = True
# app.config["TESTING"] = False


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
Session(app)
# set up login manager
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'


# silly user model
# class User(UserMixin):
#     def __init__(self, id):
#         self.id = id
#         self.name = "admin"
#         self.password = self.name
#
#     def __repr__(self):
#         return "%d/%s/%s" % (self.id, self.name, self.password)


# create some users with ids 1 to 20
# users = [User(id) for id in range(1, 21)]

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
# @app.route("/")
# def index():
#     return "Project 1: TODO"

# some protected url
@app.route('/')
@login_required
def home():
    return Response("Hello World!")


# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if password == username:
            session['logged_in'] = username
            session.modified = True
            return redirect("/")
        else:
            db.remove()
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return Response('<p>Logged out</p>')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
# @login_manager.user_loader
# def load_user(userid):
#     return User(userid)


if __name__ == "__main__":
    app.run()
