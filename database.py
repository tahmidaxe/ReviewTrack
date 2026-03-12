import sqlite3
import os
import logging
from typing import List, Dict

# The DB location usually is ~/.local/share/BackgroundFetcher/reviews.sqlite3 on the Pi
# For local testing, we fallback to our dummy 'reviews.sqlite3'
DEFAULT_DB_PATH = os.path.expanduser("~/.local/share/BackgroundFetcher/reviews.sqlite3")
LOCAL_DB_PATH = "reviews.sqlite3"

def get_db_connection():
    path_to_use = DEFAULT_DB_PATH if os.path.exists(DEFAULT_DB_PATH) else LOCAL_DB_PATH
    logging.debug(f"Connecting to database at {path_to_use}")
    
    # If standard path doesn't exist and we're on Pi, it might create an empty one.
    # It's better to ensure we only connect if we can.
    conn = sqlite3.connect(path_to_use)
    conn.row_factory = sqlite3.Row  # To return dict-like rows
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except sqlite3.Error as e:
        logging.warning(f"Failed to set WAL mode: {e}")
    return conn

def safe_get(row, key, default="N/A"):
    """Safely get a value from a sqlite3.Row, handling missing columns or NULLs."""
    try:
        val = row[key]
        return val if val is not None else default
    except IndexError:
        return default

def get_reviews_by_status(status: str) -> List[Dict]:
    """
    Fetches review items from the database by their status ('invited', 'accepted', 'completed').
    Returns a list of dictionaries with safe fallbacks.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM review_items WHERE status = ? ORDER BY id DESC", (status,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": safe_get(row, "id", -1),
                "status": safe_get(row, "status", "unknown"),
                "journal_name": safe_get(row, "journal_name", "Unknown Journal"),
                "paper_id": safe_get(row, "paper_id", "Unknown ID"),
                "paper_title": safe_get(row, "paper_title", "Untitled Paper"),
                "paper_abstract": safe_get(row, "paper_abstract", "No abstract available"),
                "date_invited": safe_get(row, "date_invited", "Unknown Date"),
                "review_due_date": safe_get(row, "review_due_date", "No Due Date"),
                "agree_link": safe_get(row, "agree_link", ""),
                "decline_link": safe_get(row, "decline_link", ""),
                "date_accepted": safe_get(row, "date_accepted", "Unknown Date"),
                "manuscript_portal_link": safe_get(row, "manuscript_portal_link", ""),
                "direct_review_link": safe_get(row, "direct_review_link", ""),
                "date_completed": safe_get(row, "date_completed", "Unknown Date")
            })
            
        conn.close()
        return results
    except Exception as e:
        logging.error(f"Error fetching reviews for status '{status}': {e}")
        return []

def get_dashboard_stats() -> Dict[str, int]:
    """
    Returns counts for invited, pending, and completed tasks for the dashboard overview.
    """
    stats = {"invited": 0, "accepted": 0, "completed": 0}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # We can do a group by
        cursor.execute("SELECT status, count(*) FROM review_items GROUP BY status")
        rows = cursor.fetchall()
        for row in rows:
            st = row[0]
            if st in stats:
                stats[st] = row[1]
                
        conn.close()
    except Exception as e:
        logging.error(f"Error fetching dashboard stats: {e}")
        
    return stats
