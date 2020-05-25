import os

from flask import Flask, Response, redirect, url_for, request, session, abort
from flask import redirect, render_template, request, session, jsonify, flash
from functools import wraps
from flask_session import Session
import random
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
## TODO: implement security features (i.e. HASHing passwords)
## TODO: AUTOMATICALLY GETBOOKS AND UPDATE DB?
## TODO: should I move some functions to a helper function
app = Flask(__name__, instance_relative_config=False)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
sesh = Session(app)
'''
# NOT_TODO:
## UNRESOLVABLE ISSUE --> if you restart the app in conda
## the browser retains the filesystem session data
## i.e. the browser will still have access to not login pages
'''
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
    print(session)
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == 'POST':
        print("post")
        user_query = db.execute("SELECT * FROM \"Users\"" +
                            " where username = :username",
                            {"username":username}).fetchone()
        flash(str(user_query))
        if user_query != None and password == user_query[2]:
            print(password,user_query[2])
            session['username'] = username
            session['logged_in'] = True
            session.modified = True
            return redirect("/")
        else:
            # TODO:
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
    session.clear()
    if request.method == 'POST':
        print("post")
        username = request.form.get("username")
        password = request.form.get("password")\
        pw_confirm = request.form.get("confirmation")
        user_query = db.execute("SELECT * FROM \"Users\"" +
                            " where username = :username",
                            {"username":username}).fetchone()
        flash(str(user_query))
        if user_query != None:
            # username already in DB
            pass
        elif not password:
            # no password provided
            pass
        elif not pw_confirm:
            pass
        elif not password == pw_confirm:
            pass
        # insert new user into DB
        db.execute("INSERT INTO users (username,password) values ()",
                     {"username":username, "password":password})
        db.commit()
        ## TODO: update page to incidate success
            ## flash bootstrap alert message ???
        ## THEN: make a hyperlink to login page
        return redirect("/login")

    else:
        # I think it will be better to
        #  display an error message on login page
        # error in login go to error page
        return render_template("register.html")

@app.route("/search", methods=["GET"])
@login_required
def search():
    book = request.args.get("book")
    if not book:
        pass
    query = "%" + book + "%"

    # Capitalize all words of input for search
    # https://docs.python.org/3.7/library/stdtypes.html?highlight=title#str.title
    query = query.title()

    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                        {"query": query})

    # Books not found
    if rows.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")

    # Fetch all the results
    results = rows.fetchall()

    # return render_template("results.html", books=results)
    pass

@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):
    print("AFDG")
    '''
        save user review and load same page with updated reviews
    '''
    if request.method == "POST":
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                         {"isbn": isbn})
        book = row.fetchone()
        bookID = book[0]
        # check for prior user submission
        row2 = ""

        if row2.rowcount == 1:
            return redirect("/book/" + isbn)

        rating = int(rating)
        # db.execute()
        # db.commit()
        # submitted message

        return redirect("/book/" + isbn)
    else:
        # row = db.execute()
        # bookinfo = row.fetchall()
        ''' good reads review '''
        api_key = ""
        query = ""
        response = ""
        bookinfo = ""
        # get books
        # row = db.execute()
        # book = row.fetchone()
        pass



@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):

    # COUNT returns rowcount
    # SUM returns sum selected cells' values
    # INNER JOIN associates books with reviews tables

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    # Error checking
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    # Fetch result from RowProxy
    tmp = row.fetchone()

    # Convert to dict
    result = dict(tmp.items())

    # Round Avg Score to 2 decimal. This returns a string which does not meet the requirement.
    # https://floating-point-gui.de/languages/python/
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)
