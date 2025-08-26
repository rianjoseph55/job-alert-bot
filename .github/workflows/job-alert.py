import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get environment variables from GitHub Secrets
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_TO = os.environ['EMAIL_TO']
QUERY = os.environ['INDEED_QUERY']
LOCATION = os.environ['INDEED_LOCATION']

# Build URL
url = f"https://www.indeed.com/jobs?q={QUERY}&l={LOCATION}&sort=date"

# Get job listings
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
jobs = soup.find_all('a', class_='tapItem', limit=5)

# Build email content
if not jobs:
    body = "No new job listings found."
else:
    body = "<h2>Recent Job Postings</h2><ul>"
    for job in jobs:
        title = job.find('h2', class_='jobTitle').text.strip()
        link = "https://www.indeed.com" + job.get('href')
        body += f"<li><a href='{link}'>{title}</a></li>"
    body += "</ul>"

# Compose email
msg = MIMEMultipart("alternative")
msg["Subject"] = "Latest Job Alerts from Indeed"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO
msg.attach(MIMEText(body, "html"))

# Send email
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print("✅ Email sent successfully.")
except Exception as e:
    print("❌ Failed to send email:", e)
