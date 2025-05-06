import sqlite3

conn = sqlite3.connect("library.db")
cur = conn.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Books table
cur.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    available INTEGER DEFAULT 1
)
""")

# Issue/Return table
cur.execute("""
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    book_id INTEGER,
    issue_date TEXT,
    return_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
)
""")

conn.commit()
conn.close()
