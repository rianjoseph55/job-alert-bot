import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os

EMAIL_FROM = os.environ.get('EMAIL_FROM')
EMAIL_TO = os.environ.get('EMAIL_TO')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
SMTP_SERVER = os.environ.get('SMTP_SERVER')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))

KEYWORDS = ["copywriter", "content strategist", "creative director"]
LOCATION = "Los Angeles"
DAYS_BACK = 3  # 72 hours

def get_posted_date_cutoff():
    return datetime.utcnow() - timedelta(days=DAYS_BACK)

def fetch_jobs():
    cutoff_date = get_posted_date_cutoff()
    all_jobs = []

    sources = [
        ("https://remotive.io/api/remote-jobs", "Remotive"),
        ("https://www.arbeitnow.com/api/job-board-api", "Arbeitnow")
    ]

    for url, source in sources:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get('jobs') or data.get('data') or []
                for job in jobs:
                    job_title = job.get("title", "").lower()
                    job_location = job.get("location", "").lower()
                    pub_date = job.get("publication_date") or job.get("created_at") or job.get("date_posted")
                    job_url = job.get("url") or job.get("job_url") or job.get("link") or job.get("job_url")

                    # Parse date string to datetime
                    if pub_date:
                        try:
                            posted_date = datetime.fromisoformat(pub_date.replace("Z", ""))
                        except:
                            continue

                        if posted_date >= cutoff_date:
                            if any(k in job_title for k in KEYWORDS) and ("remote" in job_location or "los angeles" in job_location):
                                all_jobs.append({
                                    "title": job.get("title"),
                                    "company": job.get("company_name") or job.get("company") or "Unknown",
                                    "location": job.get("location"),
                                    "url": job_url,
                                    "date": posted_date.strftime('%Y-%m-%d')
                                })
        except Exception as e:
            print(f"Error fetching from {source}: {e}")
            continue

    return all_jobs

def send_email(jobs):
    subject = "📬 Job Alert: New Matching Jobs Found" if jobs else "📭 Job Alert: No Jobs Found"
    body = ""

    if jobs:
        body += f"Found {len(jobs)} matching job(s):\n\n"
        for job in jobs:
            body += f"📌 {job['title']} at {job['company']} ({job['location']})\n🔗 {job['url']}\n📅 Posted: {job['date']}\n\n"
    else:
        body = "No new matching jobs were found in the last 72 hours."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    jobs = fetch_jobs()
    send_email(jobs)
