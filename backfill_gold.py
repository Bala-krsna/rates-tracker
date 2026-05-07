"""
One-time backfill of historical gold rates.

Pulls the 10-day history table from BankBazaar and inserts any days that
aren't already in the database. Existing rows are left alone — this script
will never overwrite or duplicate data.

Historical figures from BankBazaar's 10-day table are official end-of-day
values, so they go into the gold_22k_official / gold_24k_official columns.

Usage:
    python backfill_gold.py
"""

import sqlite3
from gold_scraper import scrape_gold_history_bangalore

DB_PATH = "data/rates.db"


def backfill():
    history = scrape_gold_history_bangalore()
    if not history:
        print("❌ No history extracted. Aborting.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0
    updated = 0

    try:
        for row in history:
            d = row["date"]
            city = row["city"]
            src = row["source"]
            r22 = row["gold_22k"]
            r24 = row["gold_24k"]

            # Does a row for this date already exist?
            cursor.execute("""
                SELECT id, gold_22k_official, gold_24k_official
                FROM gold_rates
                WHERE date = ? AND city = ? AND source = ?
            """, (d, city, src))
            existing = cursor.fetchone()

            if existing is None:
                # No row exists — insert a new one with only official values populated
                cursor.execute("""
                    INSERT INTO gold_rates
                        (date, city, source, gold_22k_official, gold_24k_official)
                    VALUES (?, ?, ?, ?, ?)
                """, (d, city, src, r22, r24))
                inserted += 1
                print(f"   ✅ Inserted {d}: 22K=₹{r22}, 24K=₹{r24}")
            else:
                row_id, existing_22, existing_24 = existing
                if existing_22 is None and existing_24 is None:
                    # Row exists but has no official values yet — fill them in
                    cursor.execute("""
                        UPDATE gold_rates
                        SET gold_22k_official = ?, gold_24k_official = ?
                        WHERE id = ?
                    """, (r22, r24, row_id))
                    updated += 1
                    print(f"   🔄 Updated {d}: filled official values")
                else:
                    # Already has official values — leave it alone
                    skipped += 1
                    print(f"   ⏭  Skipped {d}: official values already present")

        conn.commit()
        print(f"\n📊 Summary: {inserted} inserted, {updated} updated, {skipped} skipped")
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 GOLD RATE HISTORY BACKFILL")
    print("=" * 60)
    backfill()
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)