from typing import List, Dict, Any, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import ssl


def get_clients(city: str = None) -> str:
    """Look in the database to see if there are any clients at a specified city for the User to review"""
    database = {
    "Boston": [
        {
            'name': 'Lawrence Summers', 
            'email':'nishita84@gmail.com', 
            'age': 60, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University',  
            'invested_assets': 180000, 
            'last_contacted_days': 15,
            'risk_profile': 'Low',
            'estimated_available_funds': 40000, 
            'details': 'Lawrence appears to be 3 years from retirement and is estimated to have $40k in investable assets that are not invested in The Fund. Lawrence has been with The Fund for over three years and favors a low risk profile and passive management. Of the assets with The Fund, they appear to draw from a broad array of fund managers, including both The Fund-affiliated and outside funds. However, his current investment mix is stock-heavy, which may pose a risk at his age. It is recommended that Lawrence switch to a more bond-heavy investment strategy to better align with his low tolerance and nearing retirement.',
            'meeting_notes': 'In the last meeting, Lawrence expressed interest in knowing about trusts and wills for his family, and also increasing his 401k contribution. During our review this week, it was noted that one of the funds Lawrence is heavily invested in experienced a 2% decline in value over the past month.'
        },
        {
            'name': 'Peter Galison', 
            'email':'Lawrence@example.com',
            'age': 64, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University', 
            'invested_assets': 130000, 
            'last_contacted_days': 20, 
            'risk_profile': 'Low',
            'estimated_available_funds': 10000,
            'details': 'Peter has been with The Fund for two years and he favors a conservative strategy that maximizes long term profits while avoiding risk.',
            'meeting_notes': 'Peter was concerned about the current inflation rates and wanted to explore safer investment strategies. He also requested an update on his retirement plan projections.'
        },
        {
            'name': 'Eric Maskin', 
            'email':'Lawrence@example.com', 
            'age': 35, 
            'profession': 'Professor', 
            'affiliation': 'Boston University',  
            'invested_assets': 200000, 
            'last_contacted_days': 10, 
            'risk_profile': 'High',
            'estimated_available_funds': 200000,
            'details': '',
            'meeting_notes': 'Eric asked for an analysis of cryptocurrency investments. He is also considering increasing his contribution to his 401(k) plan next year.'
        },
        {
            'name': 'Catherine Dulac', 
            'email':'Lawrence@example.com',
            'age': 42, 
            'profession': 'Professor', 
            'affiliation': 'Boston College', 
            'invested_assets': 0, 
            'last_contacted_days': 0, 
            'risk_profile': 'Moderate',
            'estimated_available_funds': 1000,
            'details': '',
            'meeting_notes': 'Catherine discussed opening a 529 college savings plan for her children. She also wants advice on balancing savings and student loans.'
        },
        {
            'name': 'Gary King',
            'email':'Lawrence@example.com', 
            'age': 62, 
            'profession': 'Professor', 
            'affiliation': 'MIT', 
            'invested_assets': 80000, 
            'last_contacted_days': 50, 
            'risk_profile': 'Moderate',
            'estimated_available_funds': 5000,
            'details': '',
            'meeting_notes': 'Gary reviewed his current portfolio and discussed reallocating funds from stocks to bonds in anticipation of retirement in the next five years.'
        }
    ],
    "Chicago": [
        {
            'name': 'John Doe', 
            'email':'Lawrence@example.com',
            'age': 55, 
            'profession': 'Professor', 
            'affiliation': 'Harvard University', 
            'active_The Fund_member': True, 
            'invested_assets': 180000, 
            'last_contacted_days': 15, 
            'details': '',
            'meeting_notes': 'John expressed concern about the volatility in the tech sector and is considering shifting some assets to safer bonds. He also asked for updates on ESG (environmental, social, and governance) funds.'
        }
    ],
}

    try:
        if city:
            print("Fetching clients from", database.get(city, []))
            return json.dumps(database.get(city, []))
    except Exception as e:
        print("Error fetching client data", str(e))
        return json.dumps([])

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
    

def get_funds(risk_level: str, min_rating: int, max_expense_ratio: float, estimated_available_funds: int) -> str:
    """Retrieve funds based on given criteria"""
    database = [
        {
            'name': 'Global Growth Fund', 
            'ticker': 'GLGFX',
            'category': 'Global Large-Stock Growth', 
            'morningstar_rating': 4,
            'risk_level': 'Moderate',
            'total_return_ytd': 15.72,
            'expense_ratio': 0.0044,
            'minimum_investment': 25000
        },
        {
            'name': 'US Large Cap Value Fund', 
            'ticker': 'USLVX',
            'category': 'Large Value', 
            'morningstar_rating': 5,
            'risk_level': 'Low',
            'total_return_ytd': 9.34,
            'expense_ratio': 0.0005,
            'minimum_investment': 2500
        },
        {
            'name': 'Emerging Markets Bond Fund', 
            'ticker': 'EMBFX',
            'category': 'Emerging Markets Bond', 
            'morningstar_rating': 3,
            'risk_level': 'Low',
            'total_return_ytd': 6.21,
            'expense_ratio': 0.0004,
            'minimum_investment': 10000
        },
        {
            'name': 'Technology Sector Fund', 
            'ticker': 'TECHX',
            'category': 'Technology', 
            'morningstar_rating': 4,
            'risk_level': 'High',
            'total_return_ytd': 22.51,
            'expense_ratio': 0.0012,
            'minimum_investment': 5000
        },
        {
            'name': 'Sustainable Energy Fund', 
            'ticker': 'SUENX',
            'category': 'Alternative Energy', 
            'morningstar_rating': 5,
            'risk_level': 'Moderate',
            'total_return_ytd': 18.63,
            'expense_ratio': 0.0011,
            'minimum_investment': 1000
        }
    ]

    filtered_funds = database
    filtered_funds = [fund for fund in filtered_funds if fund['risk_level'] == risk_level]
    filtered_funds = [fund for fund in filtered_funds if fund['morningstar_rating'] >= min_rating]
    filtered_funds = [fund for fund in filtered_funds if fund['expense_ratio'] <= max_expense_ratio]
    filtered_funds = [fund for fund in filtered_funds if fund['minimum_investment'] <= estimated_available_funds]
    print('====================================')
    print('list of funds: ', filtered_funds)
    return json.dumps(filtered_funds)