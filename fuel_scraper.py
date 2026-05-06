import requests
from bs4 import BeautifulSoup
from datetime import date
import re

def scrape_fuel_bangalore():
    """Fetches today's petrol & diesel prices for Bangalore from BankBazaar."""

    petrol_url = "https://www.bankbazaar.com/fuel/petrol-price-bangalore.html"
    diesel_url = "https://www.bankbazaar.com/fuel/diesel-price-bangalore.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    petrol_price = fetch_fuel_price(petrol_url, headers, "petrol")
    diesel_price = fetch_fuel_price(diesel_url, headers, "diesel")

    result = {
        "date": date.today().isoformat(),
        "city": "Bangalore",
        "petrol": petrol_price,
        "diesel": diesel_price,
        "source": "bankbazaar.com"
    }

    print(f"\n✅ Final rates: Petrol=₹{petrol_price}/L, Diesel=₹{diesel_price}/L")
    return result


def fetch_fuel_price(url, headers, fuel_name):
    """Fetches today's fuel price from a BankBazaar fuel page."""

    print(f"\n🌐 Fetching {fuel_name} rate from {url}...")

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    print(f"✅ Page downloaded ({len(response.text)} characters)")

    soup = BeautifulSoup(response.text, "lxml")

    tables = soup.find_all("table")
    print(f"🔍 Found {len(tables)} tables on the page")

    price = None

    # Look for the daily-rates table (header has "Date")
    for idx, table in enumerate(tables):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        header_text = rows[0].get_text().lower()

        # Want the daily table with "date" in header and price/rate column
        if "date" not in header_text:
            continue
        if not any(word in header_text for word in ["price", "rate", "per litre", "per liter", "₹"]):
            continue

        print(f"📋 Using Table {idx} for {fuel_name}")

        # Get today's data (first row after header)
        data_row = rows[1]
        cells = data_row.find_all(["td", "th"])
        cell_texts = [c.get_text().strip() for c in cells]
        print(f"   Today's row: {cell_texts}")

        # Find the rupee amount in the row (skip the date cell)
        for cell in cells[1:]:
            match = re.search(r"₹?\s*([\d,]+\.\d{1,2})", cell.get_text())
            if match:
                val = float(match.group(1).replace(",", ""))
                # Sanity check: petrol/diesel typically ₹70-₹130 per litre in India
                if 50 <= val <= 200:
                    price = val
                    break

        if price:
            break

    if price is None:
        print(f"⚠️ Could not extract {fuel_name} price")
    else:
        print(f"   ✅ {fuel_name.capitalize()} = ₹{price}/L")

    return price


if __name__ == "__main__":
    print("=" * 50)
    print("Starting fuel scraper...")
    print("=" * 50)
    rates = scrape_fuel_bangalore()
    print("\n📊 Final Result:")
    print(rates)
    print("=" * 50)