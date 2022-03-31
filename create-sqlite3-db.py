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

    cursor.execute('''CREATE TABLE player (
    	id INTEGER NOT NULL,
    	colour VARCHAR,
        co VARCHAR,
        token VARCHAR,
        troops INTEGER,
        cities INTEGER,
        stars INTEGER,
        troops_value INTEGER,
        wallet INTEGER,
        game_id INTEGER,
        PRIMARY KEY (id),
        FOREIGN KEY(game_id) REFERENCES game (id)
        )''')


    conn.commit()


if __name__ == '__main__':
    create_database('aw-rpc.db')
