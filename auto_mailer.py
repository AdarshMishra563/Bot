import os
import time
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
import socket

# Load environment variables
load_dotenv()

SENDER_EMAIL = str(os.getenv("SENDER_EMAIL", "")).strip(" \"'")
SENDER_PASSWORD = str(os.getenv("SENDER_PASSWORD", "")).strip(" \"'")

# The path to your resume file
RESUME_PATH = "Resume_AdarshMishra1.pdf"

def send_email(to_email, company, role):
    if not to_email or "@" not in to_email:
        return False

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = f"Application for {role} role at {company} - Adarsh Mishra"

    # The email body
    body = f"""
Dear Hiring Team at {company},

I am writing to express my interest in the {role} position. 
I have 1 year of experience with Node.js, React, React Native, and Python, and I am highly motivated to contribute to your engineering team.

Please find my resume attached for your consideration.

Looking forward to hearing from you.

Best regards,
Adarsh Mishra
"""

    msg.attach(MIMEText(body, 'plain'))

    # Attach the resume
    try:
        with open(RESUME_PATH, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename="resume.pdf")
            msg.attach(attach)
    except FileNotFoundError:
        print(f"ERROR: Resume file not found at {RESUME_PATH}. Please put your resume there.")
        return False

    # Send the email using Gmail's SMTP server
    try:
        # Port 587 with STARTTLS is the standard for Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Auth Error for {to_email}: {e}")
        print(" -> Hint: Google blocked the Render server IP OR your App Password on Render contains a typo.")
        return False
    except Exception as e:
        print(f"Failed to send email to {to_email}: {type(e).__name__} - {e}")
        return False

def process_emails():
    try:
        df = pd.read_csv("found_jobs_enriched.csv")
    except FileNotFoundError:
        print("ERROR: found_jobs_enriched.csv not found! Run email_finder.py first.")
        return

    print(f"Loaded {len(df)} jobs. Starting email campaign...")

    if "Email_Sent" not in df.columns:
        df["Email_Sent"] = "No"

    for index, row in df.iterrows():
        if row.get("Email_Sent") == "Yes":
            continue

        email_str = row.get("HR_Email")
        company = row.get("Company Name", "Your Company")
        role = row.get("Job Title", "Software Developer")

        if pd.notna(email_str) and str(email_str).strip() != "":
            # Handle multiple emails (fallback feature from email_finder)
            email_list = [e.strip() for e in str(email_str).split(",")]
            
            # SMART FEATURE: Just send to the first valid one to avoid spam
            target_email = email_list[0]
            
            print(f"Sending email to {target_email} at {company}...")
            
            success = send_email(target_email, company, role)
            
            if success:
                print(" -> Success!")
                df.at[index, "Email_Sent"] = "Yes"
                df.to_csv("found_jobs_enriched.csv", index=False)
                # IMPORTANT: Sleep to avoid getting banned for spam
                # Waiting 5 minutes between emails is very safe
                print(" -> Waiting 5 minutes before next email...")
                time.sleep(300) 
            else:
                print(" -> Failed.")

if __name__ == "__main__":
    if not SENDER_EMAIL or SENDER_EMAIL == "your_email@gmail.com":
        print("ERROR: Please set SENDER_EMAIL and SENDER_PASSWORD in the .env file.")
    elif not os.path.exists(RESUME_PATH):
        print(f"ERROR: Please place your resume in this directory and name it '{RESUME_PATH}'.")
    else:
        # TEST THIS CAREFULLY BEFORE RUNNING
        # We process the CSV and send actual emails here
        process_emails()
