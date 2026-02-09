import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

_email_config = None

def get_email_config():
    global _email_config
    if _email_config is None:
        sender = os.getenv("EMAIL_SENDER")
        receiver = os.getenv("EMAIL_RECEIVER")
        password = os.getenv("EMAIL_PASSWORD")

        if not all([sender, receiver, password]):
            raise RuntimeError("Email environment variables are not fully set")

        _email_config = (sender, receiver, password)

    return _email_config


def _send_email(sender, receiver, password, subject, body):
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

    logger.info("Email sent: {}", subject)



def update_email(updated_items):
    sender_email, receiver_email, app_password = get_email_config()

    subject = "OCUL EZproxy Stanza Updates Detected"
    body = "The following stanzas have been updated:\n\n"

    for item in updated_items:
        body += (
            f"File: {item['filename']}\n"
            f"Title: {item['title']}\n"
            f"Date: {item['date']}\n"
            f"Link: {item['link']}\n\n"
        )

    _send_email(sender_email, receiver_email, app_password, subject, body)


def error_email(traceback_text: str):
    sender_email, receiver_email, app_password = get_email_config()

    subject = "ERROR: EZproxy stanza update job failed"
    body = (
        "The EZproxy stanza update job failed after multiple retries.\n\n"
        "Full traceback:\n\n"
        f"{traceback_text}"
    )

    _send_email(sender_email, receiver_email, app_password, subject, body)