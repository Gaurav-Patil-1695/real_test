from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: int
    full_name: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
