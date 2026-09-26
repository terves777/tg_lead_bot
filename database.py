import sqlite3

def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            service TEXT,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_lead(name: str, phone: str, service: str, username: str):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (name, phone, service, username)
        VALUES (?, ?, ?, ?)
    """, (name, phone, service, username))
    conn.commit()
    conn.close()