"""
Database operations for local.ch scraper
"""

import sqlite3
import threading
from datetime import datetime

# Thread lock for SQLite writes
db_lock = threading.Lock()


def init_database(db_path):
    """Initialize database with schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            source_url TEXT UNIQUE,
            scraped_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    return db_path


def save_business(db_path, business):
    """
    Thread-safe save business to database.
    Returns True if inserted, False if skipped (duplicate).
    """
    with db_lock:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO businesses
                (name, type, address, phone, email, website, source_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                business.get("name"),
                business.get("type"),
                business.get("address"),
                business.get("phone"),
                business.get("email"),
                business.get("website"),
                business.get("source_url"),
                business.get("scraped_at", datetime.now().isoformat())
            ))
            conn.commit()
            inserted = cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"    [DB ERROR] {e}")
            inserted = False
        finally:
            conn.close()
        return inserted


def get_stats(db_path):
    """Get database statistics."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM businesses")
    stats["total"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM businesses WHERE email IS NOT NULL AND email != ''")
    stats["with_email"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM businesses WHERE website IS NOT NULL AND website != ''")
    stats["with_website"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM businesses WHERE phone IS NOT NULL AND phone != ''")
    stats["with_phone"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM businesses WHERE type IS NOT NULL AND type != ''")
    stats["with_type"] = cursor.fetchone()[0]

    conn.close()
    return stats


def get_all_source_urls(db_path):
    """Get all source URLs from database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT source_url FROM businesses")
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    return urls


def clear_database(db_path):
    """Clear all records from database."""
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM businesses")
    conn.commit()
    conn.close()
