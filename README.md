# ✈️ PVD → RDU Flight Price Tracker

Automated flight price tracking from Providence (PVD) to Raleigh-Durham (RDU) using Google Flights data via SerpApi. Same prices you see on google.com/travel/flights, pulled automatically.

---

## Quick Start (Mac)

### Step 1 — Get your free API key

Go to **[serpapi.com](https://serpapi.com)** and click **Register** (top right). After signing up and logging in, your API key is displayed on the dashboard page.

Free tier = 250 searches/month. Running the tracker once a day uses ~30/month.

### Step 2 — Open Terminal

Press **Cmd + Space**, type **Terminal**, hit **Enter**.

### Step 3 — Install two small dependencies

Paste this and hit Enter:

```bash
pip3 install google-search-results python-dotenv
```

If you see "command not found: pip3", run this first and then retry:

```bash
python3 -m ensurepip --upgrade
```

### Step 4 — Set up the project

After downloading and unzipping the project folder:

```bash
cd ~/Downloads/flight-tracker
cp .env.example .env
nano .env
```

This opens a simple text editor. Replace `your_api_key_here` with your actual key. Then press **Ctrl + O** (save), **Enter**, **Ctrl + X** (exit).

### Step 5 — Run it

```bash
python3 tracker.py --depart 2026-07-01 --return 2026-07-07
```

You should see flight prices, airlines, stops, and durations — same data as Google Flights.

---

## Commands

```bash
# Basic price check
python3 tracker.py --depart 2026-07-01 --return 2026-07-07

# Set a price alert target
python3 tracker.py --depart 2026-07-01 --return 2026-07-07 --target 180

# Output as JSON
python3 tracker.py --depart 2026-07-01 --return 2026-07-07 --json

# View your price history log
python3 tracker.py --history

# Terminal chart of price trend
python3 dashboard.py
```

---

## Automate it (Mac)

Run it daily without thinking about it.

Open Terminal and type:

```bash
crontab -e
```

Add this line (checks prices every day at 7 AM):

```
0 7 * * * cd ~/Downloads/flight-tracker && /usr/bin/python3 tracker.py --depart 2026-07-01 --return 2026-07-07
```

Save and exit (if using vim: press `Esc`, type `:wq`, hit Enter).

---

## Email alerts (optional)

Get an email when prices drop below your target.

For Gmail:
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Generate an App Password for "Mail"
3. Fill in the SMTP fields in your `.env` file

---

## Files

| File                 | Purpose                                       |
|----------------------|-----------------------------------------------|
| `tracker.py`         | Searches Google Flights, logs prices, alerts   |
| `dashboard.py`       | Terminal chart of your price history           |
| `.env.example`       | Template — copy to `.env` and add your key     |
| `.env`               | Your credentials (git-ignored)                 |
| `price_history.json` | Auto-generated log of every price check        |

---

## Why SerpApi?

It pulls from Google Flights directly — same prices, same airlines, same results you'd see if you searched manually. The free tier is generous enough for daily tracking, and unlike other flight APIs, there's no sandbox/test mode — you get real data immediately.
---

## Troubleshooting

### Cron job fires but the tracker doesn't run (macOS)

**Symptom:** Your cron job is scheduled, the time passes, but `price_history.json` never gets updated. Manual runs from Terminal work fine.

**Root cause:** macOS uses TCC (Transparency, Consent, Control) to restrict which processes can access protected folders like Desktop, Documents, and Downloads. Unlike when you run scripts manually, cron has no way to prompt you for permission — it fails silently. This is especially common after moving the project folder into a protected location like Desktop.

**Diagnosing the issue:**

Confirm cron is actually firing (you should see entries at your scheduled time):

​```
log show --predicate 'process == "cron"' --last 7d
​```

If cron *is* firing but nothing is happening, the job itself is being blocked.

**Fix #1 — Grant Full Disk Access to cron:**

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+** button (authenticate with Touch ID / password if prompted)
3. In the file picker, press **Cmd + Shift + G** to bring up "Go to Folder"
4. Type `/usr/sbin/cron` and press Enter
5. Click **Open**, then make sure the toggle next to `cron` is ON

**Fix #2 — Enable cron logging for future debugging:**

Edit your crontab (`crontab -e`) and append `>> /full/path/to/flight-tracker/cron.log 2>&1` to the end of your job line. Example:

​```
0 18 * * * cd /Users/yourname/Desktop/flight-tracker && /usr/bin/python3 tracker.py --depart 2026-08-19 --return 2026-08-26 >> /Users/yourname/Desktop/flight-tracker/cron.log 2>&1
​```

This captures all output (and errors) to `cron.log` so you can see exactly what happened on each run.

**Testing without waiting:**

Set a temporary cron line 2–3 minutes in the future, save, wait for it to fire, then check `cron.log`. Remove the test line once verified.

### Other common errors

| Error                                | Fix                                                |
|---|---|
| `command not found: python3`         | Use full path: `/usr/bin/python3`                  |
| `No module named serpapi`            | Run `pip3 install google-search-results`           |
| `Operation not permitted` on edit    | Run `chmod 644 *.py .env.example .env`             |
| `PRICE_TARGET` SyntaxError           | Python 3.9 — ensure `global PRICE_TARGET` is at the top of `main()` |
