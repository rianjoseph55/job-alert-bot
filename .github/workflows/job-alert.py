import os
import smtplib
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load secrets from environment variables
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

# Set timeframe to look back 72 hours
now = datetime.utcnow()
threshold_time = now - timedelta(hours=72)

def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def parse_job_date(raw_date_text):
    """
    Example: 'Posted 1 day ago', 'Posted 10 hours ago'
    """
    text = raw_date_text.lower()
    try:
        if "day" in text:
            num_days = int(text.split()[1])
            return now - timedelta(days=num_days)
        elif "hour" in text:
            num_hours = int(text.split()[1])
            return now - timedelta(hours=num_hours)
        else:
            return None
    except:
        return None

def scrape_example_jobs():
    url = "https://remoteok.com/remote-copywriting-jobs"  # Update to your board
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    jobs = []
    for job in soup.select("tr.job"):
        title = job.select_one("td.position h2")
        company = job.select_one("td.company h3")
        date_posted = job.select_one("time")
        link = job.get("data-href")

        if title and company and date_posted:
            job_post_time = parse_job_date(date_posted.get_text())

            if job_post_time and job_post_time > threshold_time:
                jobs.append(f"{title.get_text(strip=True)} at {company.get_text(strip=True)}\nLink: https://remoteok.com{link}")
    
    return jobs

# Main
if __name__ == "__main__":
    jobs = scrape_example_jobs()

    if jobs:
        subject = "✅ New Jobs Found"
        body = "\n\n".join(jobs)
    else:
        subject = "📭 No Jobs Found"
        body = "The bot ran successfully, but no jobs were found in the last 72 hours."

    send_email(subject, body)
