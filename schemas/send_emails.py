from email.message import EmailMessage
from dotenv import find_dotenv, load_dotenv
import os
import smtplib

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

email_address = os.getenv("email_address")
email_password = os.getenv("email_password")



RESET_TOKEN_EXPIRE_MINUTES = 60


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