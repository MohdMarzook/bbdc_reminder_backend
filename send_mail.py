import os
import json
import base64
import datetime
from email.message import EmailMessage
from pydoc import html


from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv
load_dotenv()


BACKEND_URL = os.getenv("BACKEND_URL")

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_authenticate_from_env():

    creds_json_str = os.getenv("GMAIL_CREDENTIALS")
    token_json_str = os.getenv("GMAIL_TOKEN")

    if not creds_json_str or not token_json_str:
        print("ERROR: Gmail credentials or token not found in environment variables.")
        raise ValueError("Missing Gmail credentials in environment.")

    token_info = json.loads(token_json_str)
    

    creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    return build("gmail", "v1", credentials=creds)

def send_email_via_api(to_email: str, subject: str, html_body: str):

    print(f"Preparing to send email via Gmail API to {to_email}...")
    try:
        service = gmail_authenticate_from_env()
        
        message = EmailMessage()
        
        message.set_content(html_body, subtype='html')
        
        message["To"] = to_email
        message["From"] = "me"  # 'me' refers to the authenticated user's email
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message_body = {"raw": encoded_message}
        
        # Send the email
        send_request = (
            service.users().messages().send(userId="me", body=create_message_body).execute()
        )
        print(f'Email successfully sent! Message ID: {send_request["id"]}')
        return send_request
        
    except HttpError as error:
        print(f"An HTTP error occurred with the Gmail API: {error}")
    except ValueError as error:
        print(f"A value error occurred (likely with credentials): {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



def send_confirmation_email(to_email: str, id: str):

    subject = "Reminder Confirmation"

    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: auto; }}
            .header {{ font-size: 24px; font-weight: bold; color: #0056b3; }}
            .info {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            .button {{
                display: inline-block; padding: 10px 20px; font-size: 16px;
                color: #ffffff; background-color: #28a745; text-decoration: none;
                border-radius: 5px; margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p class="header">Confirm Your Reminder</p>
            <p>Thank you for setting up a class availability reminder!</p>
            <div class="info">
                <p><strong>To activate your reminder, please click the confirmation button below:</strong></p>
            </div>
            <div style="text-align: center;">
                <a href="{BACKEND_URL}/api/setreminder/{id}" class="button">Confirm Reminder</a>
            </div>
            <p><em>Once confirmed, we'll notify you as soon as your desired class becomes available.</em></p>
            <p style="margin-top: 30px; font-size: 12px; color: #777;">
                If you didn't request this reminder, you can safely ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

    send_email_via_api(to_email, subject, body)

def send_reminder_email(receiver_email: str, subject: str, body_data: dict):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: auto; }}
            .header {{ font-size: 24px; font-weight: bold; color: #0056b3; }}
            .details {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #0056b3; }}
            .button {{
                display: inline-block; padding: 10px 20px; font-size: 16px;
                color: #ffffff; background-color: #007bff; text-decoration: none;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p class="header">Good News!</p>
            <p>This is a friendly reminder that the class you were interested in is now available.</p>
            <div class="details">
                <p><strong>Class:</strong> {body_data.get('classSelect', 'N/A')}</p>
                <p><strong>Date & Time:</strong> {datetime.datetime.fromisoformat(body_data.get('dateTime')).strftime('%Y-%m-%d %H:%M') if body_data.get('dateTime') else 'N/A'}</p>
            </div>
            <p><strong> "{body_data.get('message', '')}", </strong><em> Please register soon to secure your spot.</em></p>
            <a href="https://booking.bbdc.sg/#/login" class="button">Book Your Spot Now</a>
            <p style="margin-top: 30px; font-size: 12px; color: #777;">Best of luck for your class</p>
        </div>
    </body>
    </html>
    """

    send_email_via_api(receiver_email, subject, html)

