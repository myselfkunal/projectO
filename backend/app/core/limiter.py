"""Rate limiter configuration for the application"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Shared limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_API}/minute"]
)
