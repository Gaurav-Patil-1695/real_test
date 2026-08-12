"""FastAPI dependencies for the auth-backend.

Provides reusable dependency callables that can be injected into route handlers
via FastAPI's dependency injection system.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# HTTP Bearer scheme
# ---------------------------------------------------------------------------
# auto_error=False so we can return a consistent 401 JSON envelope rather than
# the default FastAPI plain-text 403 when the header is absent.
# ---------------------------------------------------------------------------

_bearer_scheme: HTTPBearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer access token and return the authenticated User.

    Steps:
        1. Assert an ``Authorization: Bearer <token>`` header is present.
        2. Decode and validate the JWT (signature, expiry, type == 'access').
        3. Extract the ``sub`` claim and load the corresponding User row.
        4. Assert the user is active.

    Raises:
        HTTPException 401: On any validation failure.

    Returns:
        The authenticated :class:`app.models.user.User` ORM instance.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Could not validate credentials.",
                "details": None,
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise _unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise _unauthorized

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise _unauthorized

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise _unauthorized

    user: User | None = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        raise _unauthorized

    if not user.is_active:
        raise _unauthorized

    return user
