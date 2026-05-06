import sqlite3
import os

# Make sure the 'data' folder exists (creates it if missing)
os.makedirs("data", exist_ok=True)

# Connect to the database file (creates it if it doesn't exist yet)
conn = sqlite3.connect("data/rates.db")
cursor = conn.cursor()

# Create the gold_rates table
cursor.execute("""
CREATE TABLE IF NOT EXISTS gold_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    city TEXT NOT NULL,
    gold_22k REAL,
    gold_24k REAL,
    source TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, city, source)
)
""")

# Create the fuel_rates table
cursor.execute("""
CREATE TABLE IF NOT EXISTS fuel_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    city TEXT NOT NULL,
    petrol REAL,
    diesel REAL,
    source TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, city, source)
)
""")

# Save changes and close the connection
conn.commit()
conn.close()

print("✅ Database created successfully at data/rates.db")
print("✅ Tables created: gold_rates, fuel_rates")