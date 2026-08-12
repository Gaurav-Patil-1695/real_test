from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class RefreshToken:
    id: int
    user_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime]
    remember_me: bool
    created_at: datetime
