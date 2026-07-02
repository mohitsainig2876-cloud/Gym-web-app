import sqlite3

def init_db():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()

    # -------- CUSTOMERS --------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        date TEXT NOT NULL
    )
    """)

    # -------- PACKAGES --------
    cursor.execute("""
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    facilities TEXT,
    cost INTEGER,
    duration INTEGER   -- in days
)
""")

    # -------- PAYMENTS (FIXED) --------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount INTEGER,
        date TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    package_id INTEGER,
    start_date TEXT,
    end_date TEXT,
    status TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(package_id) REFERENCES packages(id)
)
""")

    conn.commit()
    conn.close()


# ✅ IMPORTANT (for Flask JSON support)
def get_db():
    conn = sqlite3.connect("gym.db")
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")