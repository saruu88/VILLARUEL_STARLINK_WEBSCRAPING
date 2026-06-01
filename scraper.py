import time
import csv
import os
import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Credentials ────────────────────────────────────────────────────────────────
USERNAME  = "fundamentalssystem@gmail.com"
PASSWORD  = "systemfundamentals2026"
LOGIN_URL = "https://starlink.com/auth/login"
DATA_URL  = "https://starlink.com/account/service-line/AST-2293597-46342-54?selectedDevice=ut01000000-00000000-0060d786&page=0&limit=500"
CSV_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "starlink_data_usage.csv")
DEBUG_DIR = os.path.dirname(os.path.abspath(__file__))
# ──────────────────────────────────────────────────────────────────────────────

api_data = []


def screenshot(page, name):
    path = os.path.join(DEBUG_DIR, f"debug_{name}.png")
    page.screenshot(path=path)
    print(f"  [screenshot] {path}")


def pause(message):
    print("\n" + "!" * 60)
    for line in message.strip().splitlines():
        print(f"  {line}")
    print("!" * 60)
    input("  >> Press ENTER here when done: ")
    time.sleep(2)


def handle_response(response):
    """Intercept ALL JSON network responses and save them."""
    try:
        url = response.url
        ct  = response.headers.get("content-type", "")
        if "json" in ct:
            body = response.json()
            slug = re.sub(r'[^\w]', '_', url)[-60:]
            path = os.path.join(DEBUG_DIR, f"api_{slug}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(body, f, indent=2)
            api_data.append({"url": url, "body": body})
            print(f"  [API] {url}")
    except Exception:
        pass


def parse_daily_rows(body) -> list[dict]:
    """
    Recursively search JSON for objects that have both a date/timestamp
    and a numeric usage value, then format them as daily rows.
    """
    rows = []

    def search(obj):
        if isinstance(obj, list):
            for item in obj:
                search(item)
        elif isinstance(obj, dict):
            # Look for a date key and a consumedAmountGB / usage key
            date_val  = None
            usage_val = None

            for k, v in obj.items():
                kl = k.lower()
                # Date keys
                if date_val is None and any(x in kl for x in ["date", "day", "timestamp", "time", "period", "activefrom"]):
                    if isinstance(v, str) and re.search(r'\d{4}-\d{2}-\d{2}', v):
                        date_val = v
                # Usage keys — prefer consumedAmountGB
                if usage_val is None and any(x in kl for x in ["consumedamountgb", "usagegb", "consumedgb", "datagb", "usage_gb"]):
                    try:
                        usage_val = float(v)
                    except Exception:
                        pass

            if date_val and usage_val is not None:
                # Parse ISO timestamp → M/D/YYYY
                try:
                    dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                    date_str = f"{dt.month}/{dt.day}/{dt.year}"
                except Exception:
                    date_str = date_val

                rows.append({
                    "Date": date_str,
                    "Data Usage (GB)": round(usage_val, 2)
                })
            else:
                # Recurse into nested dicts/lists
                for v in obj.values():
                    if isinstance(v, (dict, list)):
                        search(v)

    search(body)
    return rows


def run_scraper(headless: bool = False) -> str:
    global api_data
    api_data = []

    print("[*] Launching Playwright browser ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080}
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()
        page.on("response", handle_response)

        # ── Login ─────────────────────────────────────────────────────────────
        print(f"[*] Going to {LOGIN_URL} ...")
        page.goto(LOGIN_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        screenshot(page, "01_login_page")

        html = page.content().lower()
        has_email  = 'type="email"' in html or "type='email'" in html
        has_google = "google" in html
        logged_in  = False

        if has_email:
            try:
                page.fill("input[type='email']", USERNAME)
                time.sleep(0.5)
                page.fill("input[type='password']", PASSWORD)
                time.sleep(0.5)
                page.click("button[type='submit']")
                page.wait_for_url(lambda url: "auth/login" not in url, timeout=20000)
                logged_in = True
                print(f"  [+] Standard login OK: {page.url}")
            except PlaywrightTimeout:
                screenshot(page, "login_failed")

        if not logged_in and has_google:
            print("  [*] Clicking Google button ...")
            page.click("button:has-text('Google')", timeout=8000)
            time.sleep(2)

            all_pages = context.pages
            target = all_pages[-1] if len(all_pages) > 1 else page
            target.wait_for_load_state("networkidle")
            time.sleep(1)

            target.wait_for_selector("#identifierId", timeout=10000)
            target.fill("#identifierId", USERNAME)
            time.sleep(0.5)
            try:
                target.click("#identifierNext", timeout=3000)
            except Exception:
                target.evaluate("document.querySelector('#identifierNext')?.click()")
            time.sleep(2)
            target.wait_for_load_state("networkidle")

            target.wait_for_selector("input[type='password']", timeout=10000)
            target.fill("input[type='password']", PASSWORD)
            time.sleep(0.5)
            try:
                target.click("#passwordNext", timeout=3000)
            except Exception:
                target.evaluate("document.querySelector('#passwordNext')?.click()")
            time.sleep(3)
            target.wait_for_load_state("networkidle")

            try:
                target.wait_for_selector(
                    "input[type='tel'], input[aria-label*='code' i], input[aria-label*='verify' i]",
                    timeout=5000
                )
                pause(
                    "ACTION REQUIRED: Google needs a verification code!\n\n"
                    "  1. Check your Gmail inbox for the code\n"
                    "  2. Type the code in the browser window\n"
                    "  3. Click Next in the browser\n"
                    "  4. Wait until you see the Starlink account page\n"
                    "  5. Then come back here and press ENTER"
                )
            except PlaywrightTimeout:
                if "accounts.google.com" in target.url:
                    pause(
                        "ACTION REQUIRED: Google login needs your attention.\n\n"
                        "  Complete any steps in the browser, then once on\n"
                        "  the Starlink account page, press ENTER here."
                    )

            logged_in = True
            screenshot(page, "02_logged_in")

        if not logged_in:
            print("[!] Login failed.")
            browser.close()
            return ""

        # ── Load data usage page ──────────────────────────────────────────────
        print(f"[*] Loading data usage page ...")
        page.goto(DATA_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(5)
        screenshot(page, "03_data_page")

        browser.close()

    # ── Parse captured API responses ──────────────────────────────────────────
    rows = []
    print(f"\n[*] Parsing {len(api_data)} captured API response(s) ...")

    for entry in api_data:
        found = parse_daily_rows(entry["body"])
        if len(found) > len(rows):
            rows = found

    if rows:
        # Sort by date ascending
        try:
            rows.sort(key=lambda r: datetime.strptime(r["Date"], "%m/%d/%Y"))
        except Exception:
            pass

        # Write CSV
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Date", "Data Usage (GB)"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"[+] Done! CSV saved: {CSV_FILE} ({len(rows)} rows)")
        print("\nPreview:")
        for r in rows[:5]:
            print(f"  {r['Date']}  →  {r['Data Usage (GB)']} GB")
        return CSV_FILE

    print("[!] No daily data found in API responses.")
    print("[!] Check the api_*.json files in your project folder.")
    return ""


if __name__ == "__main__":
    run_scraper(headless=False)
