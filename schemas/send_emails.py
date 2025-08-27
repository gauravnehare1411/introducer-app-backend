from email.message import EmailMessage
from dotenv import find_dotenv, load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

email_address = os.getenv("email_address")
email_password = os.getenv("email_password")


RESET_TOKEN_EXPIRE_MINUTES = 60


async def send_verification_email(to_email: str, code: str):
    subject = "Verify your email"
    body = f"Your verification code is: {code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_email

    smtp_server = "smtp.hostinger.com"
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_address, email_password)
            server.send_message(msg)
            print('sent')
    except Exception as e:
        print(f"Email send failed: {e}")


def send_email(to_email: str, reset_link: str):
    """
    Send the password reset link via email.
    """
    msg = EmailMessage()

    message = f"""
Hello,

You requested to reset your password. Click the link below to reset it:
{reset_link}

This link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request a password reset, please ignore this email.

Best regards,
Your App Team
"""

    msg["Subject"] = "Reset Your Password"
    msg["From"] = email_address
    msg["To"] = to_email
    msg.set_content(message)
    
    with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)