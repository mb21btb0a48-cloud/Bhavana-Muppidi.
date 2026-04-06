import sqlite3
import os

DB_PATH = "health_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            profile_json TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS patient_tokens (
            identifier TEXT PRIMARY KEY,
            tokens_remaining INTEGER DEFAULT 1
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aadhar_number TEXT UNIQUE NOT NULL,
            mobile_number TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_user(aadhar_number: str, mobile_number: str):
    if not aadhar_number or not mobile_number: return False
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (aadhar_number, mobile_number) VALUES (?, ?)", (aadhar_number, mobile_number))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database save user error: {e}")
        return False

def check_and_deduct_token(identifier: str) -> bool:
    if not identifier: return True # Bypass strict token logic if they aren't logging in
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT tokens_remaining FROM patient_tokens WHERE identifier = ?", (identifier,))
        row = c.fetchone()
        
        if row is None:
            # New user, grant 1 free token and deduct it immediately
            c.execute("INSERT INTO patient_tokens (identifier, tokens_remaining) VALUES (?, ?)", (identifier, 0))
            conn.commit()
            conn.close()
            return True
            
        tokens = row[0]
        if tokens > 0:
            c.execute("UPDATE patient_tokens SET tokens_remaining = ? WHERE identifier = ?", (tokens - 1, identifier))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
            
    except Exception as e:
        print(f"Token error: {e}")
        return False

def save_patient_report(identifier: str, profile_json: str):
    if not identifier: return False
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO patient_reports (identifier, profile_json) VALUES (?, ?)", (identifier, profile_json))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database save error: {e}")
        return False

def get_patient_history(identifier: str):
    if not identifier: return []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, profile_json FROM patient_reports WHERE identifier = ? ORDER BY timestamp ASC", (identifier,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"Database read error: {e}")
        return []
