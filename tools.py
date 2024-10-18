from typing import List, Dict, Any, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import ssl
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

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

    
# Assuming you've already set up your Chroma DB as shown in your previous code
persist_directory = "./chromadb/financial-client-data"
collection_name = "financial-client-data"
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Chroma client
db = Chroma(persist_directory=persist_directory, embedding_function=embeddings, collection_name=collection_name)

def get_clients(city: str = None) -> str:
    """Query Chroma DB to get clients from a specified city"""
    print("clalling get clients ")
    try:
        if city:
            print("CITY,", city)
            query = f"clients in {city}"
            print("query", query)
            results = db.similarity_search(query, k=10)  # Adjust k as needed
            print("resultsa", results)
            clients = []
            for doc in results:
                if doc.metadata.get('type') == 'client' and doc.metadata.get('city') == city:
                    client_data = json.loads(doc.page_content)
                    clients.append(client_data)
                    print("final clients", clients)
            return json.dumps(clients)
        else:
            return json.dumps([])
    except Exception as e:
        print("Error fetching client data", str(e))
        return json.dumps([])

def get_funds(risk_level: str, min_rating: int, max_expense_ratio: float, estimated_available_funds: int) -> str:
    """Query Chroma DB to retrieve funds based on given criteria"""
    try:
        query = f"funds with risk level {risk_level}"
        results = db.similarity_search(query, k=20)  # Adjust k as needed
        filtered_funds = []
        for doc in results:
            if doc.metadata.get('type') == 'fund':
                fund_data = json.loads(doc.page_content)
                if (fund_data.get('risk_level') == risk_level and
                    fund_data.get('morningstar_rating', 0) >= min_rating and
                    fund_data.get('expense_ratio', float('inf')) <= max_expense_ratio and
                    fund_data.get('minimum_investment', float('inf')) <= estimated_available_funds):
                    filtered_funds.append(fund_data)
        
        if not filtered_funds:
            # Return a default fund if no matches found
            default_query = "default fund"
            default_results = db.similarity_search(default_query, k=1)
            if default_results:
                return default_results[0].page_content
            else:
                return json.dumps({})
        else:
            return json.dumps(filtered_funds)
    except Exception as e:
        print("Error fetching fund data", str(e))
        return json.dumps([])