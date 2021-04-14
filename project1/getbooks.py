'''
Query for books and add to heroku DB
'''

import os, csv
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(os.getenv("DATABASE_URL"))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))

# take csv of book titles and prep to add to db
file = open("books.csv")


data = pd.read_csv(r'books.csv')
df = pd.DataFrame(data, columns= ['isbn','title','author','year'])
# print (df)

df.to_sql('books',engine,if_exists='append')
result = db.execute("SELECT * FROM books")
[print(i) for i in result]

