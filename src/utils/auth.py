import os
import google.oauth2.credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_credentials():
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')
    refresh_token = os.getenv('GMAIL_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing Gmail API credentials in environment variables.")

    creds = google.oauth2.credentials.Credentials(
        None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds
