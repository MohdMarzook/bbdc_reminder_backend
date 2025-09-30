import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
PASSWORD = os.getenv("PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
BACKEND_URL = os.getenv("BACKEND_URL")

def send_confirmation_email(to_email, id):
    subject = "Reminder Confirmation"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: auto; }}
            .header {{ font-size: 24px; font-weight: bold; color: #0056b3; }}
            .details {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #0056b3; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: #28a745;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .info {{ 
                background-color: #e7f3ff; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 15px 0; 
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
    send_email(to_email, subject, body)

def send_reminder_email(RECEIVER_EMAIL, SUBJECT, body):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 8px; max-width: 600px; margin: auto; }}
            .header {{ font-size: 24px; font-weight: bold; color: #0056b3; }}
            .details {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #0056b3; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: #007bff;
                text-decoration: none;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p class="header">Good News!</p>
            <p>This is a friendly reminder that the class you were interested in is now available.</p>
            
            <div class="details">
                <p><strong>Class:</strong> {body['classSelect']}</p>
                <p><strong>Date & Time:</strong> {datetime.datetime.fromisoformat(body['dateTime']).strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <p><strong> "{body['message']}", </strong><em> Please register soon to secure your spot.</em></p>
            
            <a href="https://booking.bbdc.sg/#/login" class="button">Book Your Spot Now</a>
            
            <p style="margin-top: 30px; font-size: 12px; color: #777;">Best of luck for your class</p>
            
        </div>
    </body>
    </html>
    """
    send_email(RECEIVER_EMAIL, SUBJECT, html)

def send_email(RECEIVER_EMAIL, SUBJECT, body):
    print("Preparing to send email...")
    
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    message["Subject"] = SUBJECT


    message.attach(MIMEText(body, "html"))

    context = ssl.create_default_context()
    server = None  

    try:        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls(context=context)
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        
        print(f"Email successfully sent to {RECEIVER_EMAIL}!")

    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Please check your email and password.")
        print("For Gmail, you may need to use an 'App Password'.")
    except smtplib.SMTPConnectError:
        print(f"Failed to connect to the server at {SMTP_SERVER}.")
    except Exception as e:        
        print(f"An error occurred: {e}")

    finally:        
        if server:
            print("Closing connection.")
            server.quit()

