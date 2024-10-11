# create_database.py
import os
import sqlite3


def create_database():
    # Specify the directory where the SQLite database will be created
    database_dir = os.getcwd()  # Current working directory

    # Ensure the directory exists
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)

    # Specify the path to the SQLite database file
    database_path = os.path.join(database_dir, "family_photos.db")

    # Flag to indicate if the database is new
    is_new_database = not os.path.exists(database_path)

    # Create a connection to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Create the people table if it doesn't exist
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

    # Create the photos table if it doesn't exist
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

    # Check if 'is_profile_photo' column exists in 'photos' table, and add it if it doesn't
    cursor.execute("PRAGMA table_info(photos);")
    columns = [column_info[1] for column_info in cursor.fetchall()]
    if "is_profile_photo" not in columns:
        cursor.execute(
            "ALTER TABLE photos ADD COLUMN is_profile_photo INTEGER DEFAULT 0"
        )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    # if is_new_database:
    #     print("Database and tables created successfully!")
    # else:
    #     print("Database already exists. Ensured tables and columns are up to date.")
