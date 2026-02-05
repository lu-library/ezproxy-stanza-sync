import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


OCUL_URL = "https://help.oclc.org/Library_Management/EZproxy/EZproxy_database_stanzas/Database_stanzas/EZproxy_database_stanzas_most_recent"
BASE_URL = "https://help.oclc.org"

# ====== CONFIG ======

# Set to None to use today's date automatically
#CHECK_DATE = None
# Or set manually like "2024-01-01" for testing
CHECK_DATE = "2024-01-01"

# ===== EMAIL NOTIFICATION =====
def send_email(updated_items):
    sender_email = os.getenv("EMAIL_SENDER")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    app_password = os.getenv("EMAIL_PASSWORD")
    subject = "OCUL EZproxy Stanza Updates Detected"

    body = "The following stanzas have been updated:\n\n"

    for item in updated_items:
        body += (
            f"File: {item['filename']}\n"
            f"Title: {item['title']}\n"
            f"Date: {item['date']}\n"
            f"Link: {item['link']}\n\n"
        )

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

# ====================

with open("mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
# Titles we care about
target_titles = set(t.lower() for t in mapping.values())

if CHECK_DATE:
    check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
else:
    check_date = datetime.today().date()

print(f"Checking updates since: {check_date}\n")

resp = requests.get(OCUL_URL, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# =========================
# Compare using mapping
# =========================

updated_items = []
title_to_file = {v.lower(): k for k, v in mapping.items()}
updated_amount = 0

# === Find the correct section by h3 title ===

target_h3 = None
for h3 in soup.find_all("h3"):
    if "Recently updated database stanzas" in h3.get_text():
        target_h3 = h3
        break

if not target_h3:
    print("Could not find recent updates section.")
    exit()

# The table should follow the h3
table = target_h3.find_next("table")

if not table:
    print("No table found after recent updates header.")
    exit()

# === Parse table rows ===

for row in table.find_all("tr"):
    cols = row.find_all("td")
    if len(cols) < 2:
        continue

    a = cols[0].find("a")
    if not a:
        continue

    title = a.get_text(strip=True)
    link = a.get("href")
    date_text = cols[1].get_text(strip=True)

    if title.lower() not in target_titles:
        continue

    try:
        update_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        continue

    if update_date >= check_date:
        if link.startswith("/"):
            link = BASE_URL + link

        filename = title_to_file.get(title.lower(), "UNKNOWN")
        updated_items.append({
            "filename": filename,
            "title": title,
            "date": str(update_date),
            "link": link
        })
        updated_amount+=1

# ===== OUTPUT =====

if not updated_items:
    print("No updates found.")
else:
    print("Updated stanzas:",updated_amount,"\n")

    # Send email notification
    send_email(updated_items)

    for item in updated_items:
        print(f"File: {item['filename']}")
        print(f"Title: {item['title']}")
        print(f"Date: {item['date']}")
        print(f"Link: {item['link']}\n")
