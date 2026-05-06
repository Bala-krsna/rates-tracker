import sqlite3

conn = sqlite3.connect("data/rates.db")
cur = conn.cursor()

# Check existing columns first so we don't error out if already added
cur.execute("PRAGMA table_info(gold_rates)")
existing_cols = [row[1] for row in cur.fetchall()]
print("Existing columns:", existing_cols)

if "gold_22k_official" not in existing_cols:
    cur.execute("ALTER TABLE gold_rates ADD COLUMN gold_22k_official REAL")
    print("✅ Added gold_22k_official")
else:
    print("• gold_22k_official already exists")

if "gold_24k_official" not in existing_cols:
    cur.execute("ALTER TABLE gold_rates ADD COLUMN gold_24k_official REAL")
    print("✅ Added gold_24k_official")
else:
    print("• gold_24k_official already exists")

conn.commit()
conn.close()
print("Done.")