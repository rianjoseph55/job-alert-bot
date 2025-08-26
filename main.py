import feedparser
import json
import requests
from pathlib import Path
from email.message import EmailMessage
import smtplib
from datetime import datetime

# --------- Config ---------
KEYWORDS = [
    "copywriter",
    "content writer",
    "copy supervisor",
    "associate creative director",
    "acd"
]

LOCATIONS = [
    "remote",
    "los angeles",
    "hybrid"
]

EMAIL_FROM = "your.email@gmail.com"         # Set this in GitHub Secrets
EMAIL_TO = "your.email@gmail.com"           # Set this in GitHub Secrets
EMAIL_PASSWORD = "app_password_here"        # Set this in GitHub Secrets

SEEN_FILE = "seen.json"

# --------- Sources ---------
INDEED_FEEDS = [
    "https://www.indeed.com/rss?q=copywriter+OR+content+writer+OR+copy+supervisor+OR+associate+creative+director&l=Remote",
    "https://www.indeed.com/rss?q=copywriter+OR+content+writer+OR+copy+supervisor+OR+associate+creative+director&l=Los+Angeles%2C+CA"
]

GREENHOUSE_COMPANIES = [
    "wiedenkennedy", "dentsu", "vice", "rga", "publicisgroupe", "ogilvy",
    "bbdo", "adamandeve", "mother", "goodeggs", "figagency", "voxmedia",
    "caa", "spotify", "snap"
]

LEVER_COMPANIES = [
    "airbnb", "dropbox", "discord", "doordash", "robinhood", "calm",
    "figma", "peloton", "canva", "clearbit", "reddit", "webflow"
]

# --------- Utils ---------
def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def match(title, location):
    title = title.lower()
    location = location.lower() if location else ""
    return (
        any(k in title for k in KEYWORDS) and
        any(loc in location for loc in LOCATIONS)
    )

def send_email(new_jobs):
    msg = EmailMessage()
    msg.set_content("\n\n".join(f"{j['title']}\n{j['link']}\n({j['source']})" for j in new_jobs))
    msg["Subject"] = f"🧠 {len(new_jobs)} New Creative Jobs"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

# --------- Main ---------
def main():
    seen = load_seen()
    new_jobs = []

    # --- INDEED RSS ---
    for feed_url in INDEED_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            location = entry.get("location", "remote")
            if link not in seen and match(title, location):
                new_jobs.append({"title": title, "link": link, "source": "Indeed"})
                seen.add(link)

    # --- GREENHOUSE API ---
    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            jobs = res.json().get("jobs", [])
            for job in jobs:
                title = job.get("title", "")
                location = job.get("location", {}).get("name", "")
                link = job.get("absolute_url", "")
                if link and link not in seen and match(title, location):
                    new_jobs.append({"title": title, "link": link, "source": company})
                    seen.add(link)
        except Exception as e:
            print(f"[Greenhouse:{company}] Error: {e}")

    # --- LEVER API ---
    for company in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            for job in res.json():
                title = job.get("text", "")
                location = job.get("categories", {}).get("location", "")
                link = job.get("hostedUrl", "")
                if link and link not in seen and match(title, location):
                    new_jobs.append({"title": title, "link": link, "source": company})
                    seen.add(link)
        except Exception as e:
            print(f"[Lever:{company}] Error: {e}")

    # --- Notify ---
    if new_jobs:
        send_email(new_jobs)
        print(f"[{datetime.now()}] ✅ Sent {len(new_jobs)} job(s).")
        save_seen(seen)
    else:
        print(f"[{datetime.now()}] No new jobs.")

if __name__ == "__main__":
    main()

