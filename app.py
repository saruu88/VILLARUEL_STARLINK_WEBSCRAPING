import os
import csv
import threading
from flask import Flask, render_template, jsonify, send_file
from scraper import run_scraper, CSV_FILE

app = Flask(__name__)

# Track background scrape job
scrape_status = {"running": False, "message": "Idle", "success": None}


def _scrape_job():
    scrape_status["running"] = True
    scrape_status["message"] = "Scraping in progress…"
    scrape_status["success"] = None
    try:
        path = run_scraper(headless=True)
        if path:
            scrape_status["message"] = f"Scrape complete! Data saved to {os.path.basename(path)}."
            scrape_status["success"] = True
        else:
            scrape_status["message"] = "Scrape finished but no data was found. Check credentials or page structure."
            scrape_status["success"] = False
    except Exception as exc:
        scrape_status["message"] = f"Error: {exc}"
        scrape_status["success"] = False
    finally:
        scrape_status["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    if scrape_status["running"]:
        return jsonify({"status": "already_running", "message": "Scrape is already in progress."})
    thread = threading.Thread(target=_scrape_job, daemon=True)
    thread.start()
    return jsonify({"status": "started", "message": "Scrape job started."})


@app.route("/api/scrape-status")
def api_scrape_status():
    return jsonify(scrape_status)


@app.route("/api/data")
def api_data():
    if not os.path.exists(CSV_FILE):
        return jsonify({"rows": [], "message": "No CSV file found. Run the scraper first."})
    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return jsonify({"rows": rows, "message": f"{len(rows)} records loaded."})


@app.route("/api/download-csv")
def api_download_csv():
    if not os.path.exists(CSV_FILE):
        return jsonify({"error": "CSV not found."}), 404
    return send_file(CSV_FILE, as_attachment=True, download_name="starlink_data_usage.csv")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
