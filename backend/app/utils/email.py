import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)


async def send_verification_email(email: str, token: str, username: str) -> bool:
    """Send email verification link using SendGrid"""
    try:
        if not settings.SENDGRID_API_KEY:
            if settings.ENVIRONMENT == "production":
                logger.error("SendGrid API key missing; cannot send verification email in production")
                return False
            logger.warning("SendGrid API key missing; logging token for development only")
            logger.info(f"🔐 VERIFICATION TOKEN FOR {email}: {token}")
            return True

        verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; background-color: white; margin: 0 auto; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; text-align: center;">Welcome to UniLink, {username}! 🎉</h2>
                    <p style="color: #666; line-height: 1.6;">Thank you for registering. Please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        If the button doesn't work, copy and paste this link:<br>
                        <code style="background-color: #f0f0f0; padding: 8px; display: inline-block; margin-top: 10px;">{verification_link}</code>
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                        ⏰ This link will expire in 24 hours.<br>
                        If you didn't create this account, please ignore this email.
                    </p>
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px;">
                        Best regards,<br>
                        <strong>UniLink Team</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=Email(settings.EMAIL_FROM),
            to_emails=To(email),
            subject="Verify Your UniLink Account",
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"✅ Verification email sent to {email} (Status: {response.status_code})")
        return response.status_code == 202  # 202 = Accepted

    except Exception as e:
        logger.error(f"❌ Error sending verification email to {email}: {str(e)}")
        return False


async def send_password_reset_email(email: str, token: str, username: str) -> bool:
    """Send password reset email using SendGrid"""
    try:
        if not settings.SENDGRID_API_KEY:
            if settings.ENVIRONMENT == "production":
                logger.error("SendGrid API key missing; cannot send password reset email in production")
                return False
            logger.warning("SendGrid API key missing; logging reset token for development only")
            logger.info(f"🔐 PASSWORD RESET TOKEN FOR {email}: {token}")
            return True

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; background-color: white; margin: 0 auto; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; text-align: center;">Reset Your UniLink Password</h2>
                    <p style="color: #666; line-height: 1.6;">Hi {username},</p>
                    <p style="color: #666; line-height: 1.6;">We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #FF9800; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Link expires in 1 hour.<br>
                        If you didn't request this, ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=Email(settings.EMAIL_FROM),
            to_emails=To(email),
            subject="Reset Your UniLink Password",
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"✅ Password reset email sent to {email}")
        return response.status_code == 202

    except Exception as e:
        logger.error(f"❌ Error sending password reset email: {str(e)}")
        return False


async def send_login_otp_email(email: str, otp: str, username: str) -> bool:
    """Send login OTP email using SendGrid"""
    try:
        if not settings.SENDGRID_API_KEY:
            if settings.ENVIRONMENT == "production":
                logger.error("SendGrid API key missing; cannot send login OTP email in production")
                return False
            logger.warning("SendGrid API key missing; logging OTP for development only")
            logger.info(f"🔐 LOGIN OTP FOR {email}: {otp}")
            return True

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; background-color: white; margin: 0 auto; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; text-align: center;">Your UniLink Login Code</h2>
                    <p style="color: #666; line-height: 1.6;">Hi {username},</p>
                    <p style="color: #666; line-height: 1.6;">Use the code below to finish logging in:</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <div style="display: inline-block; font-size: 28px; letter-spacing: 6px; font-weight: bold; background: #f0f0f0; padding: 12px 20px; border-radius: 6px;">
                            {otp}
                        </div>
                    </div>

                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This code expires in 10 minutes.<br>
                        If you didn't request this, you can ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.EMAIL_FROM),
            to_emails=To(email),
            subject="Your UniLink Login Code",
            html_content=html_content
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"✅ Login OTP email sent to {email} (Status: {response.status_code})")
        return response.status_code == 202

    except Exception as e:
        logger.error(f"❌ Error sending login OTP email to {email}: {str(e)}")
        return False


def generate_verification_token() -> str:
    """Generate a random verification token"""
    import secrets
    return secrets.token_urlsafe(32)


def generate_otp_code(length: int = 6) -> str:
    """Generate numeric OTP code"""
    import secrets
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
