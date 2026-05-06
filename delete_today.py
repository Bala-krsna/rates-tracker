import sqlite3, os
here = os.path.dirname(os.path.abspath(__file__))
db = os.path.join(here, "data", "rates.db")
c = sqlite3.connect(db)

today = '2026-05-06'
for table in ('gold_rates', 'fuel_rates'):
    cur = c.execute(f"DELETE FROM {table} WHERE date = ?", (today,))
    print(f"Deleted {cur.rowcount} row(s) from {table}")

c.commit()
c.close()
print("Done.")