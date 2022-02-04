'''This script sets up the test database for the unittests
   in the github CI/CD runner virtual environment.'''


import sqlite3
from sqlite3 import Error


def create_database(db_file):
    """Create a database with tables."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)

    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE game (
    	id INTEGER NOT NULL,
    	token VARCHAR NOT NULL,
    	date DATETIME,
    	updated DATETIME,
    	board VARCHAR,
    	PRIMARY KEY (id),
    	UNIQUE (token)
        )''')


    conn.commit()


if __name__ == '__main__':
    create_database('aw-rpc.db')
