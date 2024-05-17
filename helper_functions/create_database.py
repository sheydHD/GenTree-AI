# create_database.py
import os
import sqlite3


def create_database():
    # Specify the directory where the SQLite database will be created
    database_dir = (
        os.getcwd()
    )  # This will set database_dir to the current working directory

    # Create the directory if it doesn't exist
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)

    # Specify the path to the SQLite database file
    database_path = os.path.join(database_dir, "family_photos.db")

    # Check if the database file exists
    if not os.path.exists(database_path):
        # Create a connection to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Create the people table with additional columns
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                connected_to INTEGER,
                FOREIGN KEY (connected_to) REFERENCES people(id)
            )
            """
        )

        # Create the photos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER,
                photo BLOB,
                FOREIGN KEY (person_id) REFERENCES people(id)
            )
            """
        )

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print("Database and tables created successfully!")
