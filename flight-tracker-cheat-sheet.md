# ✈️ Flight Tracker — Quick Reference

All commands assume you're in the flight-tracker folder first.
Open Terminal and start with:

```
cd ~/Desktop/flight-tracker
```

---

## Check prices right now

```
python3 tracker.py --depart 2026-08-19 --return 2026-08-26
```

## Check different dates

```
python3 tracker.py --depart YYYY-MM-DD --return YYYY-MM-DD
```

## Set a custom price target (e.g. alert below $180)

```
python3 tracker.py --depart 2026-08-19 --return 2026-08-26 --target 180
```

## View your price history log

```
python3 tracker.py --history
```

## See a price trend chart

```
python3 dashboard.py
```

## Output raw JSON (for pasting into a spreadsheet, etc.)

```
python3 tracker.py --depart 2026-08-19 --return 2026-08-26 --json
```

---

## Automation (cron)

**View your scheduled job:**

```
crontab -l
```

**Edit your scheduled job:**

```
crontab -e
```

Then press i to edit, make changes, press Esc, type :wq, hit Enter.

**Current cron line (runs daily at 7 AM):**

```
0 7 * * * cd /Users/home/Desktop/flight-tracker && /usr/bin/python3 tracker.py --depart 2026-08-19 --return 2026-08-26
```

**Change the time** — the first two numbers are minute and hour:

```
0 7 * * *    → 7:00 AM
30 6 * * *   → 6:30 AM
0 18 * * *   → 6:00 PM
0 7,18 * * * → 7 AM and 6 PM (twice daily)
```

**Remove automation entirely:**

```
crontab -r
```

---

## Viewing JSON files

**From Terminal (raw):**

```
cat price_history.json
```

**From Terminal (nicely formatted):**

```
python3 -m json.tool price_history.json
```

**From Finder:** Right-click the file → Open With → TextEdit

**Set TextEdit as default for all JSON files:** Right-click → Get Info → Open with → TextEdit → Change All

**Export to spreadsheet (opens in Numbers):**

```
python3 -c "
import json, csv
data = json.load(open('price_history.json'))
with open('price_history.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Date Checked', 'Route', 'Depart', 'Return', 'Best Price', 'Offers Found'])
    for row in data:
        w.writerow([row['checked_at'][:16], row['route'], row['depart'], row['return'], row['best_price'], row['num_offers']])
print('Saved to price_history.csv')
" && open price_history.csv
```

---

## Edit your settings

```
nano .env
```

- SERPAPI_KEY — your API key
- PRICE_TARGET — default alert threshold (currently 200)
- ORIGIN / DESTINATION — airport codes (currently PVD / RDU)
- SMTP fields — fill in for email alerts (optional)

Save: Ctrl + O, Enter, Ctrl + X

---

## If something breaks

**"command not found: python3"**

```
/usr/bin/python3 tracker.py --depart ...
```

**"No module named serpapi"**

```
pip3 install google-search-results
```

**"Operation not permitted"**

```
chmod 644 *.py .env.example .env
```

**Check if cron is still set up after a restart:**

```
crontab -l
```
