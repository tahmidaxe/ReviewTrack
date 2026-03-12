import sqlite3
import os
from datetime import datetime, timedelta

def create_db():
    db_path = "reviews.sqlite3"
    
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    # Enable WAL mode for concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    
    cursor = conn.cursor()
    
    # Create the review_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            journal_name TEXT,
            paper_id TEXT,
            paper_title TEXT,
            paper_abstract TEXT,
            date_invited TEXT,
            review_due_date TEXT,
            agree_link TEXT,
            decline_link TEXT,
            date_accepted TEXT,
            manuscript_portal_link TEXT,
            direct_review_link TEXT,
            date_completed TEXT,
            last_updated TEXT
        )
    """)
    
    now = datetime.now()
    
    # Insert some Dummy Data
    
    # 1. Invited
    cursor.execute("""
        INSERT INTO review_items (status, journal_name, paper_id, paper_title, paper_abstract, date_invited, review_due_date, agree_link, decline_link, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "invited",
        "IEEE Transactions on Neural Networks",
        "TNNLS-2023-1042",
        "A Novel Approach to Efficient Deep Learning Inference on Edge Devices",
        "This paper presents a new quantization method...",
        (now - timedelta(days=1)).isoformat(),
        (now + timedelta(days=14)).strftime("%Y-%m-%d"),
        "http://example.com/agree/1042",
        "http://example.com/decline/1042",
        now.isoformat()
    ))
    
    cursor.execute("""
        INSERT INTO review_items (status, journal_name, paper_id, paper_title, date_invited, agree_link, decline_link, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "invited",
        "Nature Machine Intelligence",
        "NMI-24-0012",
        "Federated Learning with Differential Privacy Guarantees",
        (now - timedelta(hours=5)).isoformat(),
        "http://example.com/agree/0012",
        "http://example.com/decline/0012",
        now.isoformat()
    ))
    
    # 2. Accepted (Pending)
    cursor.execute("""
        INSERT INTO review_items (status, journal_name, paper_id, paper_title, date_accepted, review_due_date, manuscript_portal_link, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "accepted",
        "ACM Computing Surveys",
        "CSUR-23-089",
        "A Comprehensive Survey of Large Language Models",
        (now - timedelta(days=4)).isoformat(),
        (now + timedelta(days=10)).strftime("%Y-%m-%d"),
        "http://portal.example.com/login",
        now.isoformat()
    ))

    cursor.execute("""
        INSERT INTO review_items (status, journal_name, paper_id, paper_title, date_accepted, review_due_date, direct_review_link, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "accepted",
        "Journal of Artificial Intelligence Research",
        "JAIR-8091",
        "Reinforcement Learning under Sparse Rewards",
        (now - timedelta(days=10)).isoformat(),
        (now + timedelta(days=2)).strftime("%Y-%m-%d"),
        "http://portal.example.com/direct/8091",
        now.isoformat()
    ))
    
    # 3. Completed
    cursor.execute("""
        INSERT INTO review_items (status, journal_name, paper_id, paper_title, date_completed, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "completed",
        "IEEE Access",
        "ACCESS-22-10045",
        "IoT Security Protocols: A Case Study",
        (now - timedelta(days=45)).isoformat(),
        now.isoformat()
    ))

    
    conn.commit()
    conn.close()
    print(f"Created dummy database at {db_path} with 5 records.")

if __name__ == "__main__":
    create_db()
