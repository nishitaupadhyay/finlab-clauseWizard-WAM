import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import ssl
from typing import Optional

def send_email_gmail(recipient_email: str, subject: str, body: str) -> str:
    # Gmail SMTP settings
    smtp_server = "smtp.gmail.com"
    port = 465  # For SSL
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")  # This should now be your App Password

    if not gmail_user or not gmail_password:
        return "Error: Gmail credentials are missing. Please check your .env file."

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = gmail_user
    message["To"] = recipient_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        print(f"Attempting to connect to {smtp_server}:{port} using SSL...")
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            print("SSL connection established. Logging in...")
            server.login(gmail_user, gmail_password)
            print("Logged in successfully. Sending email...")
            
            server.send_message(message)
            result = f"Email sent successfully to {recipient_email} from {gmail_user}"
            print(result)
            return result
    except smtplib.SMTPAuthenticationError:
        error_message = "SMTP Authentication failed. Please check your Gmail credentials and ensure you're using the correct App Password."
        print(error_message)
        return error_message
    except smtplib.SMTPException as e:
        error_message = f"SMTP error occurred: {str(e)}"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        print(error_message)
        return error_message