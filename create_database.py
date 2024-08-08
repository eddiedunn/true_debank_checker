#!/usr/bin/env python
"""
This script creates a SQLite database using a provided schema file.

It includes a function to:
- Create a database and execute the schema script to set up the database structure.

Functions:
- create_database: Connects to a SQLite database, reads the schema from a file, and executes it.

Usage:
- Run this script directly to create the database with the specified name and schema file.

Example:
    $ python create_database.py

Dependencies:
- sqlite3

Attributes:
- db_name (str): The name of the database file to be created.
- schema_file (str): The path to the SQL schema file.
"""

import sqlite3
from app.config import DB_FILE
from app.config import SCHEMA_FILE

def create_database(db_name: str, schema_file: str):
    """
    Create a SQLite database using the provided schema file.

    Args:
        db_name (str): The name of the database file to create.
        schema_file (str): The path to the SQL schema file.

    This function connects to the specified SQLite database (or creates it if it doesn't exist),
    reads the SQL schema from the provided file, and executes the schema to set up the database
    structure. The connection is then committed and closed.
    """
    conn = sqlite3.connect(db_name)
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema = f.read()

    conn.executescript(schema)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database(DB_FILE, SCHEMA_FILE)
