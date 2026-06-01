# Starlink Data Usage Webscraper

A Python-based web scraper that logs into Starlink's website, extracts daily data usage, saves it to a CSV file, and presents it through a Flask web dashboard.

---

## Project Structure

```
starlink-webscraper/
├── app.py               # Flask web application
├── scraper.py           # Playwright scraper logic
├── requirements.txt     # Python dependencies
├── templates/
│   └── index.html       # Web UI dashboard
└── starlink_data_usage.csv   # Output CSV (generated after scrape)
```

---

## Requirements

- Python 3.10+
- Google Chrome installed
- pip (Python package manager)

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/starlink-webscraper.git
cd VILLARUEL_STARLINK_WEBSCRAPING
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `playwright install` Install the required browser binaries

---

## Running the Application

### Option A — Web Dashboard (recommended)

```bash
python app.py
```

Then open your browser at: **http://127.0.0.1:5000**

1. Click **▶ Run Scraper** to start scraping live data from Starlink.
2. Wait for the status badge to show **Scrape complete!**
3. The chart and table will populate automatically.
4. Click **⬇ Download CSV** to save the data locally.

### Option B — Scraper only (no UI)

```bash
python scraper.py
```

This runs the scraper and saves `starlink_data_usage.csv` in the project folder.

---

## Output CSV Format

| Date       | Data Usage (GB) |
|------------|----------------|
| 5/17/2026  | 22.83          |
| 5/18/2026  | 18.45          |
| ...        | ...            |

---

## Dependencies Explained

| Package           | Purpose                                      |
|-------------------|----------------------------------------------|
| flask             | Web framework for the dashboard UI           |
| playwright        | Modern browser automation for web scraping   |

---

## Notes

- To watch the browser in action, edit `scraper.py` and set `headless=False` in `run_scraper()`.
- Credentials are stored in `scraper.py` — do **not** share or commit them publicly.
- If the scraper cannot detect the page layout, it saves `page_source.html` and `data_usage_page.png` in the project folder for debugging.
