import os

log_path = os.path.join(os.path.dirname(__file__), "chromedriver.log")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())
else:
    print("chromedriver.log not found in this folder")
