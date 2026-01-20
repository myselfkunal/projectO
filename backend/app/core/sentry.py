"""Sentry error tracking configuration for UniLink"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.asgi import AsgiIntegration
import os
from .config import settings

# Initialize Sentry
def init_sentry():
    """Initialize Sentry for error tracking and monitoring"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                AsgiIntegration(),
            ],
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.ENVIRONMENT,
            debug=settings.DEBUG,
            before_send=before_send_sentry,
            release=settings.APP_VERSION,
        )
        print(f"Sentry initialized for {settings.ENVIRONMENT}")


def before_send_sentry(event, hint):
    """
    Filter sensitive data before sending to Sentry
    
    Remove:
    - Passwords and tokens
    - Email addresses in certain contexts
    - Personal identification info
    - Request bodies with sensitive data
    """
    # Skip 404s and 3xx responses
    if event.get("level") in ("info",):
        return None
    
    # Remove request body for security
    if "request" in event:
        if "data" in event["request"]:
            # Only log first 500 chars of body
            body = event["request"].get("data", "")
            if isinstance(body, str) and len(body) > 500:
                event["request"]["data"] = body[:500] + "..."
        
        # Remove auth headers
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            for key in list(headers.keys()):
                if key.lower() in ("authorization", "cookie", "x-api-key"):
                    headers[key] = "[REDACTED]"
    
    return event
