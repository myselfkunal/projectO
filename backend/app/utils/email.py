import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def send_verification_email(email: str, token: str, username: str) -> bool:
    """Send email verification link to user (or print to logs for testing)"""
    try:
        # FOR TESTING: Print token to console/logs
        logger.info(f"🔐 VERIFICATION TOKEN FOR {email}: {token}")
        print(f"\n{'='*60}")
        print(f"VERIFICATION TOKEN FOR {email}")
        print(f"Token: {token}")
        print(f"{'='*60}\n")

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials missing; skipping email send in dev mode")
            return True
        
        subject = "Verify Your UniLink Account"
        verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Welcome to UniLink, {username}!</h2>
                <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Verify Email</a></p>
                <p>Or copy and paste this link: {verification_link}</p>
                <p>This link will expire in 24 hours.</p>
                <p>Best regards,<br>UniLink Team</p>
            </body>
        </html>
        """
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = email
        
        message.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, email, message.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def generate_verification_token() -> str:
    """Generate a random verification token"""
    import secrets
    return secrets.token_urlsafe(32)
