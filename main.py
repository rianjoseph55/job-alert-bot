import feedparser
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime

RSS_FEEDS = [
    "https://www.indeed.com/rss?q=copywriter+OR+content+writer+OR+copy+supervisor+OR+associate+creative+director&l=Remote",
    "https://www.indeed.com/rss?q=copywriter+OR+content+writer+OR+copy+supervisor+OR+associate+creative+director&l=Los+Angeles%2C+CA"
]

KEYWORDS = ["copywriter", "content writer", "copy supervisor", "associate creative director", "acd"]
SEEN_FILE = "seen.json"

EMAIL_FROM = "your.email@gmail.com"
EMAIL_TO = "your.email@gmail.com"
EMAIL_PASSWORD = "your-app-password"

def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_email(new_jobs):
    msg = EmailMessage()
    msg.set_content("\n\n".join(f"{j['title']}\n{j['link']}" for j in new_jobs))
    msg["Subject"] = f"🧠 {len(new_jobs)} New Creative Job(s)"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

def main():
    seen = load_seen()
    new_jobs = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title.lower()
            link = entry.link
            if any(k in title for k in KEYWORDS) and link not in seen:
                new_jobs.append({"title": entry.title, "link": link})
                seen.add(link)

    if new_jobs:
        send_email(new_jobs)
        save_seen(seen)
        print(f"[{datetime.now()}] ✅ Sent {len(new_jobs)} new jobs.")
    else:
        print(f"[{datetime.now()}] No new jobs found.")

if __name__ == "__main__":
    main()
