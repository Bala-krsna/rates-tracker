import sqlite3, os
here = os.path.dirname(os.path.abspath(__file__))
db = os.path.join(here, "data", "rates.db")
print("Looking for:", db)
print("Exists?", os.path.exists(db))
c = sqlite3.connect(db)
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", tables)
for (table,) in tables:
    print(f"\n--- Last 5 rows of {table} ---")
    for row in c.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 5"):
        print(row)