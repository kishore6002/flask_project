import sqlite3

def init_db():
    db = sqlite3.connect("database.db")
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT,
        dept TEXT,
        role TEXT
    )
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS allotments (
        dept TEXT,
        year TEXT,
        section TEXT,
        room TEXT,
        day TEXT
    )
    """)

    db.commit()
    db.close()

    print("Database ready")

