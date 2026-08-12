"""Rate limiting utilities (NFR-08).

Provides SlowAPI-based limiters for the login and forgot-password endpoints.
Limits are driven by environment settings so they can be tuned without code
changes.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

# ---------------------------------------------------------------------------
# Shared limiter instance
# ---------------------------------------------------------------------------
# Uses the client's remote IP address as the rate-limit key.  The limiter is
# configured with a default limit that applies when no per-route override is
# supplied; individual endpoint decorators use the specific limit strings
# defined below.
# ---------------------------------------------------------------------------

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)

# ---------------------------------------------------------------------------
# Per-endpoint limit strings
# ---------------------------------------------------------------------------
# These are derived from settings so that ops can adjust them via env vars
# without touching source code.  The format follows SlowAPI / limits notation:
# "<count> per <period>"  e.g. "5 per minute".
# ---------------------------------------------------------------------------

LOGIN_LIMIT: str = settings.LOGIN_RATE_LIMIT
FORGOT_PASSWORD_LIMIT: str = settings.FORGOT_PASSWORD_RATE_LIMIT
