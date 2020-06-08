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
## TODO: should I move some functions to a helper function
## TODO: ADD HOME BUTTON TO PAGES
## TODO: ADD BOOTSTRAP ELEMentss
## what happens to reviews when you delete a user?
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
        # print(session)
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
    username = request.form.get("username")
    password = request.form.get("password")
    if request.method == 'POST':
        print("post")
        user_query = db.execute("SELECT * FROM users" +
                            " where username = :username",
                            {"username":username}).fetchone()
        # flash(str(user_query))
        if user_query != None and password == user_query[2]:
            print(password,user_query[2])
            session['username'] = username
            session['user_id'] = user_query[0]
            session['logged_in'] = True
            # session.modified = True
            return redirect("/")
        else:
            # TODO:
            message = ""
            if "" in (username,password): message += "Username cannot be empty. \n"
            if user_query is None: message += "User does not exist \n"
            elif password != user_query[2]: message += "Incorrect Password \n"
            # I think it will be better to
            #  display an error message on login page
            # error in login go to error page
            # return abort(401)
            print(message)
            flash(message)
            # return redirect('/login')
            return render_template("login.html")
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
        password = request.form.get("password")
        pw_confirm = request.form.get("confirmation")

        user_query = db.execute("SELECT * FROM users" +
        " where username = :username",
        {"username":username}).fetchone()

        # flash(str(user_query))
        if not username or username == "":
            return render_template("register.html",user_msg="please provide a username")
        elif user_query is not None:
            # username already in DB
            return render_template("register.html",message="username in DB Already")
        elif not password:
            # no password provided
            return render_template("register.html",pw_msg="please provide a password")
        elif not pw_confirm:

            return render_template("register.html",confirm_msg="please confirm Password")
        elif not password == pw_confirm:

            return render_template("register.html",message="passwords do not match")
        # insert new user into DB
        db.execute("INSERT INTO users (username,password) values (:username,:password)",
                     {"username":username, "password":password})
        db.commit()

        ## MAYBE: flash bootstrap alert message ???
        return render_template("register.html",message="register  success!",success=True)

    else:

        return render_template("register.html")

@app.route("/search", methods=["GET"])
@login_required
def search():
    book = request.args.get("book")
    ## # TODO: separate search to four for isbn title author year
    if not book:
        pass
    query = "%" + book + "%"

    # Capitalize all words of input for search
    # https://docs.python.org/3.7/library/stdtypes.html?highlight=title#str.title
    query = query.title()
    print(query)
    # # TODO: ADD % to each word manually

    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 10",
                        {"query": query})
    print(rows.rowcount)
    # Books not found
    if rows.rowcount == 0:
        return render_template("index.html", message="we can't find books with that description.")

    # Fetch all the results
    results = rows.fetchall()

    return render_template("searchresults.html", books=results)

@app.route("/book/<isbn>",methods=["GET","POST"])
@login_required
def book(isbn):
    '''
        save user review and load same page with updated reviews
    '''
    if request.method == "POST":
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        row = db.execute("SELECT index FROM books WHERE isbn = :isbn",
                         {"isbn": isbn})
        book = row.fetchone()
        bookID = book[0]
        # check for prior user submission
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id" +
                          " AND book_id = CAST(:book_id as varchar(10))",
                          {"user_id": currentUser, "book_id":bookID})
        # a review already counts
        print(row2.rowcount)
        if row2.rowcount > 0:
            ## GO TO ERROR.HTML AND GIVE A REDIRECT BACK TO THIS BOOK
            flash('you have already reviewed this book')
            return render_template("error.html", message="please try again",link="/book/"+isbn)
            # return redirect("/book/" + isbn)

        rating = int(rating)
        db.execute("INSERT INTO reviews (user_id, book_id, text, rating) VALUES \
                    (:user_id, :book_id, :text, :rating)",
                    {"user_id": currentUser,
                    "book_id": bookID,
                    "text": comment,
                    "rating": rating})
        db.commit()

        
        return redirect("/book/" + isbn)
    else:
        ## METHOD == GET --> REVIEWS FOR BOOK(USING ISBN CODE AND API)

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})
        bookinfo = row.fetchall()
        ''' good reads review '''
        api_key = os.getenv("GOODREADS_KEY")
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": api_key, "isbns": isbn})
        response = query.json()
        response = response['books'][0]
        bookinfo.append(response)

        # get books
        row = db.execute("SELECT CAST(index as varchar(10)) FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})
        book = row.fetchone()[0]
        results = db.execute("SELECT users.username, text, rating, \
                            to_char(date, 'DD Mon YY - HH24:MI:SS') as time \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id \
                            WHERE reviews.book_id = :book \
                            ORDER BY time",
                            {"book": book})

        reviews = results.fetchall()

        return render_template("bookpage.html", bookInfo=bookinfo, reviews=reviews)



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
                    ON CAST(books.index as varchar(10)) = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn}).fetchone()
    print(row)
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
