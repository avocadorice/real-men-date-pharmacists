import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            via TEXT,
            description TEXT,
            salary TEXT,
            apply_link TEXT,
            posted_at TEXT,
            distance_miles REAL,
            status TEXT DEFAULT 'new', -- 'new', 'seen', 'applied', 'archived', 'rejected'
            notes TEXT,
            fetched_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            applied_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
