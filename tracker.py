#!/usr/bin/env python3
"""
PVD → RDU Flight Price Tracker
================================
Tracks round-trip flight prices from Providence (PVD) to Raleigh-Durham (RDU)
using SerpApi's Google Flights engine — same prices you see on Google Flights.

Setup:
  1. Sign up free at https://serpapi.com (click Register, top right)
  2. Go to your dashboard → copy your API key
  3. Copy .env.example → .env and paste your key
  4. pip3 install google-search-results python-dotenv
  5. Run: python3 tracker.py --depart 2026-07-01 --return 2026-07-07

Free tier: 100 searches/month (once a day = ~30/month, plenty of room).
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import datetime, date
from email.mime.text import MIMEText
from pathlib import Path

try:
    from serpapi import GoogleSearch
except ImportError:
    print("Missing dependency. Run:\n  pip3 install google-search-results")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env support is optional


# ─── Configuration ────────────────────────────────────────────────────────────

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

ORIGIN = os.getenv("ORIGIN", "PVD")
DESTINATION = os.getenv("DESTINATION", "RDU")
PRICE_TARGET = float(os.getenv("PRICE_TARGET", "200"))
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "price_history.json"))
CURRENCY = "USD"

# Email alerts (optional)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")


# ─── Search Google Flights via SerpApi ────────────────────────────────────────

def search_flights(depart: str, return_date: str, adults: int = 1) -> dict:
    """
    Query Google Flights through SerpApi.
    Returns the raw API response as a dict.
    """
    if not SERPAPI_KEY:
        print("ERROR: Set SERPAPI_KEY in your .env file.")
        print("Sign up free at https://serpapi.com")
        sys.exit(1)

    params = {
        "api_key": SERPAPI_KEY,
        "engine": "google_flights",
        "departure_id": ORIGIN,
        "arrival_id": DESTINATION,
        "outbound_date": depart,
        "return_date": return_date,
        "adults": adults,
        "currency": CURRENCY,
        "hl": "en",
        "type": "1",  # 1 = round trip
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            print(f"API error: {results['error']}")
            return {}

        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return {}


def parse_offers(results: dict) -> list[dict]:
    """
    Parse SerpApi Google Flights response into a clean list.
    Google Flights returns 'best_flights' and 'other_flights'.
    """
    offers = []

    for category in ["best_flights", "other_flights"]:
        flights = results.get(category, [])
        for flight in flights:
            price = flight.get("price")
            if price is None:
                continue

            legs = flight.get("flights", [])

            def summarize_leg(leg):
                return {
                    "airline": leg.get("airline", "?"),
                    "flight_number": leg.get("flight_number", ""),
                    "departure_airport": leg.get("departure_airport", {}).get("id", ""),
                    "departure_time": leg.get("departure_airport", {}).get("time", ""),
                    "arrival_airport": leg.get("arrival_airport", {}).get("id", ""),
                    "arrival_time": leg.get("arrival_airport", {}).get("time", ""),
                    "duration": leg.get("duration", 0),
                    "airplane": leg.get("airplane", ""),
                }

            total_duration = flight.get("total_duration", 0)
            stops = len(legs) - 1 if legs else 0
            airlines = list({leg.get("airline", "?") for leg in legs})

            # Format duration as Xh Ym
            hours, mins = divmod(total_duration, 60)
            duration_str = f"{hours}h {mins:02d}m" if total_duration else "?"

            offers.append({
                "price": price,
                "currency": CURRENCY,
                "airlines": airlines,
                "stops": stops,
                "total_duration": duration_str,
                "legs": [summarize_leg(leg) for leg in legs],
                "category": "Best" if category == "best_flights" else "Other",
                "carbon_kg": flight.get("carbon_emissions", {}).get("this_flight", 0) // 1000
                             if flight.get("carbon_emissions") else None,
            })

    offers.sort(key=lambda x: x["price"])
    return offers


# ─── Price History ────────────────────────────────────────────────────────────

def load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(history: list):
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def record_prices(depart: str, return_date: str, offers: list[dict]):
    """Append today's best price to the history log."""
    history = load_history()
    if not offers:
        return history

    entry = {
        "checked_at": datetime.now().isoformat(),
        "route": f"{ORIGIN}→{DESTINATION}",
        "depart": depart,
        "return": return_date,
        "best_price": offers[0]["price"],
        "num_offers": len(offers),
        "top_3": [
            {
                "price": o["price"],
                "airlines": o["airlines"],
                "stops": o["stops"],
                "duration": o["total_duration"],
            }
            for o in offers[:3]
        ],
    }
    history.append(entry)
    save_history(history)
    return history


# ─── Alerts ───────────────────────────────────────────────────────────────────

def check_alert(offers: list[dict], depart: str, return_date: str):
    """Send email if best price is at or below target."""
    if not offers:
        return
    best = offers[0]["price"]
    if best > PRICE_TARGET:
        print(f"  Best price ${best} is above ${PRICE_TARGET:.0f} target. No alert.")
        return

    print(f"  🎯 PRICE ALERT: ${best} is at/below your ${PRICE_TARGET:.0f} target!")

    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_EMAIL]):
        print("  (Email not configured — see .env.example to enable alerts)")
        return

    subject = f"✈️ PVD→RDU ${best} — below your ${PRICE_TARGET:.0f} target"
    body = (
        f"Flight deal found!\n\n"
        f"Route: {ORIGIN} → {DESTINATION}\n"
        f"Dates: {depart} → {return_date}\n"
        f"Price: ${best}\n"
        f"Airlines: {', '.join(offers[0]['airlines'])}\n"
        f"Stops: {offers[0]['stops']}\n"
        f"Duration: {offers[0]['total_duration']}\n\n"
        f"Top 3 options:\n"
    )
    for i, o in enumerate(offers[:3], 1):
        body += f"  {i}. ${o['price']} — {', '.join(o['airlines'])} ({o['stops']} stop(s), {o['total_duration']})\n"
    body += f"\nGo to Google Flights to book: https://www.google.com/travel/flights?q=flights+from+{ORIGIN}+to+{DESTINATION}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print("  ✉️  Alert email sent.")
    except Exception as e:
        print(f"  Email error: {e}")


# ─── Display ──────────────────────────────────────────────────────────────────

def print_results(offers: list[dict], depart: str, return_date: str):
    print(f"\n{'='*60}")
    print(f"  ✈️  {ORIGIN} → {DESTINATION}")
    print(f"  📅  {depart}  →  {return_date}")
    print(f"  🔍  {len(offers)} offers found at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    if not offers:
        print("  No flights found for these dates.\n")
        return

    for i, o in enumerate(offers, 1):
        airlines = ", ".join(o["airlines"])
        tag = " ⭐ BEST" if i == 1 else ""
        carbon = f" · {o['carbon_kg']}kg CO₂" if o.get("carbon_kg") else ""

        print(f"  #{i}  ${o['price']}{tag}")
        print(f"       {airlines} · {o['stops']} stop(s) · {o['total_duration']}{carbon}")

        # Show individual legs
        for leg in o["legs"]:
            dep_time = leg["departure_time"].split(" ")[-1] if " " in leg["departure_time"] else leg["departure_time"]
            arr_time = leg["arrival_time"].split(" ")[-1] if " " in leg["arrival_time"] else leg["arrival_time"]
            leg_hrs, leg_mins = divmod(leg["duration"], 60)
            print(f"       └ {leg['flight_number']} {leg['departure_airport']}→{leg['arrival_airport']} {dep_time}–{arr_time} ({leg_hrs}h{leg_mins:02d}m)")
        print()


def print_history_summary():
    history = load_history()
    if not history:
        return
    prices = [h["best_price"] for h in history]
    print(f"  📊 Price history ({len(history)} checks)")
    print(f"     Low: ${min(prices)}  |  High: ${max(prices)}  |  Avg: ${sum(prices)/len(prices):.0f}")
    if len(prices) >= 2:
        diff = prices[-1] - prices[-2]
        arrow = "↓" if diff < 0 else "↑" if diff > 0 else "→"
        print(f"     Last change: {arrow} ${abs(diff)}")
    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    global PRICE_TARGET

    parser = argparse.ArgumentParser(
        description="Track PVD→RDU flight prices (via Google Flights)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tracker.py --depart 2026-07-01 --return 2026-07-07
  python3 tracker.py --depart 2026-07-01 --return 2026-07-07 --target 180
  python3 tracker.py --history
        """,
    )
    parser.add_argument("--depart", help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    parser.add_argument("--target", type=float, help=f"Price alert threshold (default: ${PRICE_TARGET:.0f})")
    parser.add_argument("--adults", type=int, default=1, help="Number of passengers")
    parser.add_argument("--history", action="store_true", help="Show price history only")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.target:
        PRICE_TARGET = args.target

    if args.history:
        history = load_history()
        if not history:
            print("No price history yet. Run a search first.")
        else:
            print(json.dumps(history, indent=2))
        return

    if not args.depart or not args.return_date:
        parser.error("--depart and --return are required (unless using --history)")

    # Validate dates
    try:
        d = date.fromisoformat(args.depart)
        r = date.fromisoformat(args.return_date)
        if r <= d:
            parser.error("Return date must be after departure date")
        if d < date.today():
            parser.error("Departure date must be in the future")
    except ValueError as e:
        parser.error(f"Invalid date format: {e}")

    results = search_flights(args.depart, args.return_date, args.adults)
    offers = parse_offers(results)

    if args.json:
        print(json.dumps(offers, indent=2))
    else:
        print_results(offers, args.depart, args.return_date)
        record_prices(args.depart, args.return_date, offers)
        print_history_summary()
        check_alert(offers, args.depart, args.return_date)


if __name__ == "__main__":
    main()
