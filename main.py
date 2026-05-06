import sqlite3
from gold_scraper import scrape_gold_bangalore
from fuel_scraper import scrape_fuel_bangalore

DB_PATH = "data/rates.db"


from datetime import datetime, timedelta

def save_gold_rates(rates):
    """
    Two-pass save:
      1) Upsert TODAY's row with the live rate just scraped.
      2) Update YESTERDAY's row with BankBazaar's 'official' yesterday figure
         so the trend matches the website's own historical display.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        today = rates["date"]
        yesterday = (datetime.strptime(today, "%Y-%m-%d")
                     - timedelta(days=1)).strftime("%Y-%m-%d")
        city = rates["city"]
        source = rates["source"]

        # ---- 1. TODAY: upsert live rate ----
        cursor.execute("""
            SELECT id FROM gold_rates
            WHERE date = ? AND city = ? AND source = ?
        """, (today, city, source))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE gold_rates
                SET gold_22k = ?, gold_24k = ?, scraped_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (rates["gold_22k"], rates["gold_24k"], existing[0]))
            print(f"💾 Today's live gold rate updated (id {existing[0]})")
        else:
            cursor.execute("""
                INSERT INTO gold_rates (date, city, gold_22k, gold_24k, source)
                VALUES (?, ?, ?, ?, ?)
            """, (today, city, rates["gold_22k"], rates["gold_24k"], source))
            print(f"💾 Today's live gold rate inserted (id {cursor.lastrowid})")

        # ---- 2. YESTERDAY: lock in BankBazaar's official figure ----
        y22 = rates.get("gold_22k_yesterday")
        y24 = rates.get("gold_24k_yesterday")

        if y22 is not None and y24 is not None:
            cursor.execute("""
                SELECT id FROM gold_rates
                WHERE date = ? AND city = ? AND source = ?
            """, (yesterday, city, source))
            yrow = cursor.fetchone()

            if yrow:
                cursor.execute("""
                    UPDATE gold_rates
                    SET gold_22k_official = ?, gold_24k_official = ?
                    WHERE id = ?
                """, (y22, y24, yrow[0]))
                print(f"🔒 Yesterday's official gold rate locked (id {yrow[0]}): "
                      f"22K=₹{y22}, 24K=₹{y24}")
            else:
                # No row exists for yesterday yet — create one with only
                # the official values populated. live columns stay NULL.
                cursor.execute("""
                    INSERT INTO gold_rates
                        (date, city, source, gold_22k_official, gold_24k_official)
                    VALUES (?, ?, ?, ?, ?)
                """, (yesterday, city, source, y22, y24))
                print(f"🔒 Yesterday's official gold rate inserted "
                      f"(id {cursor.lastrowid}): 22K=₹{y22}, 24K=₹{y24}")
        else:
            print("⚠️ Scraper did not return yesterday's rate; skipping official update.")

        conn.commit()
    finally:
        conn.close()

def save_fuel_rates(rates):
    """Save fuel rates dict into the fuel_rates table. Overwrites if same date+city+source exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM fuel_rates
            WHERE date = ? AND city = ? AND source = ?
        """, (rates["date"], rates["city"], rates["source"]))
        deleted = cursor.rowcount

        cursor.execute("""
            INSERT INTO fuel_rates (date, city, petrol, diesel, source)
            VALUES (?, ?, ?, ?, ?)
        """, (
            rates["date"],
            rates["city"],
            rates["petrol"],
            rates["diesel"],
            rates["source"],
        ))
        conn.commit()
        if deleted:
            print(f"💾 Fuel rates updated (replaced existing row, new id: {cursor.lastrowid})")
        else:
            print(f"💾 Fuel rates saved to database (row id: {cursor.lastrowid})")
    finally:
        conn.close()

def show_recent_data():
    """Print the last 5 entries from each table for confirmation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("📊 LAST 5 GOLD ENTRIES")
    print("=" * 60)
    cursor.execute("""
        SELECT date, city, gold_22k, gold_24k,
               gold_22k_official, gold_24k_official, source
        FROM gold_rates
        ORDER BY date DESC, id DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        date_, city, l22, l24, o22, o24, src = row
        live = f"22K=₹{l22} 24K=₹{l24}" if l22 is not None else "—"
        off = (f"22K=₹{o22} 24K=₹{o24}"
               if o22 is not None and o24 is not None else "—")
        print(f"   {date_} | {city} | live: {live} | official: {off} | {src}")

    print("\n" + "=" * 60)
    print("⛽ LAST 5 FUEL ENTRIES")
    print("=" * 60)
    cursor.execute("""
        SELECT date, city, petrol, diesel, source
        FROM fuel_rates
        ORDER BY date DESC, id DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} | {row[1]} | Petrol=₹{row[2]} | Diesel=₹{row[3]} | {row[4]}")

    conn.close()

def main():
    print("=" * 60)
    print("🚀 STARTING DAILY RATE TRACKER")
    print("=" * 60)

    # 1. Scrape gold
    try:
        gold = scrape_gold_bangalore()
        if gold["gold_22k"] and gold["gold_24k"]:
            save_gold_rates(gold)
        else:
            print("⚠️ Gold scrape returned None values, not saving.")
    except Exception as e:
        print(f"❌ Gold scraping failed: {e}")

    # 2. Scrape fuel
    try:
        fuel = scrape_fuel_bangalore()
        if fuel["petrol"] and fuel["diesel"]:
            save_fuel_rates(fuel)
        else:
            print("⚠️ Fuel scrape returned None values, not saving.")
    except Exception as e:
        print(f"❌ Fuel scraping failed: {e}")

    # 3. Show recent data
    show_recent_data()

    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()