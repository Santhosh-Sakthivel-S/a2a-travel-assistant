import smtplib
from email.message import EmailMessage
from strands import tool
from src.config.settings import settings, logger

@tool
def send_email(to_email: str, subject: str, body: str) -> str:
    """Send the generated itinerary using SMTP."""
    if not all([settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD]):
        logger.error("Email credentials are missing.")
        return f"System Error: Cannot send email to {to_email} due to missing credentials."

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = settings.EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        logger.info(f"Attempting to send email to: {to_email}")
        # Using Gmail's default SMTP settings
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Successfully sent itinerary to {to_email}")
        return f"Successfully sent email to {to_email}"
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return f"Failed to send email: {str(e)}"