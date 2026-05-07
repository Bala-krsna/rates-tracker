import requests
from bs4 import BeautifulSoup
from datetime import date
import re

def scrape_gold_bangalore():
    """Fetches today's gold rates for Bangalore from BankBazaar.

    BankBazaar shows daily prices per 8 grams. We extract today's row
    and divide by 8 to get the per-gram rate.
    """

    url = "https://www.bankbazaar.com/gold-rate-bangalore.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"🌐 Fetching gold rates from {url}...")

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    print(f"✅ Page downloaded ({len(response.text)} characters)")

    soup = BeautifulSoup(response.text, "lxml")

    gold_22k = None
    gold_24k = None
    grams_per_unit = None
    gold_22k_yesterday = None
    gold_24k_yesterday = None


    tables = soup.find_all("table")
    print(f"🔍 Found {len(tables)} tables on the page")

    # Find the daily-rates table (the one with 'Date' column and 8-gram prices)
    for idx, table in enumerate(tables):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        header_text = rows[0].get_text().lower()

        # We want the daily table — header has "date" and gram-quantity info
        if "date" not in header_text:
            continue
        if not ("22" in header_text and "24" in header_text):
            continue

        print(f"📋 Using Table {idx} (daily rates)")

        # Detect grams in the header (e.g., "8 grams", "10 grams", "1 gram")
        gram_match = re.search(r"(\d+)\s*gram", header_text)
        if gram_match:
            grams_per_unit = int(gram_match.group(1))
            print(f"   Detected unit: per {grams_per_unit} grams")
        else:
            grams_per_unit = 1
            print("   Could not detect unit, assuming per 1 gram")

        # ---- Today's row ----
        today_row = rows[1]
        today_cells = today_row.find_all(["td", "th"])
        print(f"   Today's row:     {[c.get_text().strip() for c in today_cells]}")

        if len(today_cells) >= 3:
            m22 = re.search(r"₹\s*([\d,]+)", today_cells[1].get_text())
            m24 = re.search(r"₹\s*([\d,]+)", today_cells[2].get_text())
            if m22:
                gold_22k = round(float(m22.group(1).replace(",", "")) / grams_per_unit, 2)
            if m24:
                gold_24k = round(float(m24.group(1).replace(",", "")) / grams_per_unit, 2)

        # ---- Yesterday's row (BankBazaar's own "official" yesterday figure) ----
        if len(rows) >= 3:
            yest_row = rows[2]
            yest_cells = yest_row.find_all(["td", "th"])
            print(f"   Yesterday's row: {[c.get_text().strip() for c in yest_cells]}")

            if len(yest_cells) >= 3:
                m22y = re.search(r"₹\s*([\d,]+)", yest_cells[1].get_text())
                m24y = re.search(r"₹\s*([\d,]+)", yest_cells[2].get_text())
                if m22y:
                    gold_22k_yesterday = round(
                        float(m22y.group(1).replace(",", "")) / grams_per_unit, 2)
                if m24y:
                    gold_24k_yesterday = round(
                        float(m24y.group(1).replace(",", "")) / grams_per_unit, 2)

        break
    result = {
        "date": date.today().isoformat(),
        "city": "Bangalore",
        "gold_22k": gold_22k,
        "gold_24k": gold_24k,
        "gold_22k_yesterday": gold_22k_yesterday,    # NEW
        "gold_24k_yesterday": gold_24k_yesterday,    # NEW
        "source": "bankbazaar.com"
    }

    print(f"\n✅ Final rates (per gram): "
          f"today 22K=₹{gold_22k}, 24K=₹{gold_24k} | "
          f"yesterday 22K=₹{gold_22k_yesterday}, 24K=₹{gold_24k_yesterday}")
    return result
def scrape_gold_history_bangalore():
    """Fetches the entire 10-day gold rate history from BankBazaar.

    Returns a list of dicts, each with date and per-gram 22K/24K rates.
    These come from BankBazaar's 'Last 10 days' table — official end-of-day figures.
    """
    from datetime import datetime

    url = "https://www.bankbazaar.com/gold-rate-bangalore.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    print(f"🌐 Fetching gold history from {url}...")
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    history = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        header_text = rows[0].get_text().lower()
        if "date" not in header_text:
            continue
        if not ("22" in header_text and "24" in header_text):
            continue

        # Detect grams unit from the header
        gram_match = re.search(r"(\d+)\s*gram", header_text)
        grams_per_unit = int(gram_match.group(1)) if gram_match else 1

        # Loop through every data row (skipping header at index 0)
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue

            date_text = cells[0].get_text().strip()
            m22 = re.search(r"₹\s*([\d,]+)", cells[1].get_text())
            m24 = re.search(r"₹\s*([\d,]+)", cells[2].get_text())
            if not (m22 and m24):
                continue

            # Try to parse the date string (e.g., "06 May 2026", "06 May, 2026")
            parsed_date = None
            for fmt in ("%d %b %Y", "%d %b, %Y", "%d %B %Y", "%d %B, %Y"):
                try:
                    parsed_date = datetime.strptime(date_text, fmt).date().isoformat()
                    break
                except ValueError:
                    continue
            if not parsed_date:
                print(f"   ⚠️ Could not parse date: '{date_text}' — skipping")
                continue

            rate_22k = round(float(m22.group(1).replace(",", "")) / grams_per_unit, 2)
            rate_24k = round(float(m24.group(1).replace(",", "")) / grams_per_unit, 2)

            history.append({
                "date": parsed_date,
                "city": "Bangalore",
                "gold_22k": rate_22k,
                "gold_24k": rate_24k,
                "source": "bankbazaar.com",
            })
        break

    print(f"✅ Extracted {len(history)} days of history")
    return history

if __name__ == "__main__":
    print("=" * 50)
    print("Starting gold scraper...")
    print("=" * 50)
    rates = scrape_gold_bangalore()
    print("\n📊 Final Result:")
    print(rates)
    print("=" * 50)