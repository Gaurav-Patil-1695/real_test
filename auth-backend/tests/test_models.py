import pytest
from datetime import datetime
from typing import Optional
import sys
import os

# Ensure the source root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models.user import User
from app.models.refresh_token import RefreshToken


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime(2024, 1, 15, 12, 0, 0)
LATER = datetime(2024, 6, 30, 23, 59, 59)


@pytest.fixture
def valid_user():
    return User(
        id=1,
        full_name="Alice Example",
        email="alice@example.com",
        password_hash="hashed_password_abc123",
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def valid_refresh_token():
    return RefreshToken(
        id=10,
        user_id=1,
        token_hash="token_hash_xyz",
        expires_at=LATER,
        revoked_at=None,
        remember_me=False,
        created_at=NOW,
    )


# ---------------------------------------------------------------------------
# User tests
# ---------------------------------------------------------------------------

class TestUser:

    def test_user_creation_stores_all_fields(self, valid_user):
        assert valid_user.id == 1
        assert valid_user.full_name == "Alice Example"
        assert valid_user.email == "alice@example.com"
        assert valid_user.password_hash == "hashed_password_abc123"
        assert valid_user.is_active is True
        assert valid_user.created_at == NOW
        assert valid_user.updated_at == NOW

    def test_user_is_active_false(self):
        user = User(
            id=2,
            full_name="Bob Inactive",
            email="bob@example.com",
            password_hash="some_hash",
            is_active=False,
            created_at=NOW,
            updated_at=NOW,
        )
        assert user.is_active is False

    def test_user_equality_same_fields(self):
        u1 = User(
            id=1,
            full_name="Alice Example",
            email="alice@example.com",
            password_hash="hashed_password_abc123",
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )
        u2 = User(
            id=1,
            full_name="Alice Example",
            email="alice@example.com",
            password_hash="hashed_password_abc123",
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )
        assert u1 == u2

    def test_user_inequality_different_id(self, valid_user):
        other = User(
            id=999,
            full_name="Alice Example",
            email="alice@example.com",
            password_hash="hashed_password_abc123",
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )
        assert valid_user != other

    def test_user_field_mutation(self, valid_user):
        valid_user.email = "new_email@example.com"
        assert valid_user.email == "new_email@example.com"

    def test_user_updated_at_can_differ_from_created_at(self):
        user = User(
            id=3,
            full_name="Carol",
            email="carol@example.com",
            password_hash="hash",
            is_active=True,
            created_at=NOW,
            updated_at=LATER,
        )
        assert user.created_at < user.updated_at

    def test_user_is_dataclass(self, valid_user):
        import dataclasses
        assert dataclasses.is_dataclass(valid_user)

    def test_user_empty_full_name(self):
        user = User(
            id=4,
            full_name="",
            email="no_name@example.com",
            password_hash="hash",
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )
        assert user.full_name == ""

    def test_user_password_hash_is_string(self, valid_user):
        assert isinstance(valid_user.password_hash, str)

    def test_user_id_integer(self, valid_user):
        assert isinstance(valid_user.id, int)

    def test_user_created_at_is_datetime(self, valid_user):
        assert isinstance(valid_user.created_at, datetime)

    def test_user_updated_at_is_datetime(self, valid_user):
        assert isinstance(valid_user.updated_at, datetime)


# ---------------------------------------------------------------------------
# RefreshToken tests
# ---------------------------------------------------------------------------

class TestRefreshToken:

    def test_refresh_token_creation_stores_all_fields(self, valid_refresh_token):
        assert valid_refresh_token.id == 10
        assert valid_refresh_token.user_id == 1
        assert valid_refresh_token.token_hash == "token_hash_xyz"
        assert valid_refresh_token.expires_at == LATER
        assert valid_refresh_token.revoked_at is None
        assert valid_refresh_token.remember_me is False
        assert valid_refresh_token.created_at == NOW

    def test_refresh_token_revoked_at_set(self):
        token = RefreshToken(
            id=11,
            user_id=2,
            token_hash="another_hash",
            expires_at=LATER,
            revoked_at=LATER,
            remember_me=True,
            created_at=NOW,
        )
        assert token.revoked_at == LATER

    def test_refresh_token_revoked_at_none(self, valid_refresh_token):
        assert valid_refresh_token.revoked_at is None

    def test_refresh_token_remember_me_true(self):
        token = RefreshToken(
            id=12,
            user_id=3,
            token_hash="hash_remember",
            expires_at=LATER,
            revoked_at=None,
            remember_me=True,
            created_at=NOW,
        )
        assert token.remember_me is True

    def test_refresh_token_remember_me_false(self, valid_refresh_token):
        assert valid_refresh_token.remember_me is False

    def test_refresh_token_equality(self):
        t1 = RefreshToken(
            id=10,
            user_id=1,
            token_hash="token_hash_xyz",
            expires_at=LATER,
            revoked_at=None,
            remember_me=False,
            created_at=NOW,
        )
        t2 = RefreshToken(
            id=10,
            user_id=1,
            token_hash="token_hash_xyz",
            expires_at=LATER,
            revoked_at=None,
            remember_me=False,
            created_at=NOW,
        )
        assert t1 == t2

    def test_refresh_token_inequality_different_id(self, valid_refresh_token):
        other = RefreshToken(
            id=99,
            user_id=1,
            token_hash="token_hash_xyz",
            expires_at=LATER,
            revoked_at=None,
            remember_me=False,
            created_at=NOW,
        )
        assert valid_refresh_token != other

    def test_refresh_token_is_dataclass(self, valid_refresh_token):
        import dataclasses
        assert dataclasses.is_dataclass(valid_refresh_token)

    def test_refresh_token_user_id_integer(self, valid_refresh_token):
        assert isinstance(valid_refresh_token.user_id, int)

    def test_refresh_token_token_hash_is_string(self, valid_refresh_token):
        assert isinstance(valid_refresh_token.token_hash, str)

    def test_refresh_token_expires_at_is_datetime(self, valid_refresh_token):
        assert isinstance(valid_refresh_token.expires_at, datetime)

    def test_refresh_token_created_at_is_datetime(self, valid_refresh_token):
        assert isinstance(valid_refresh_token.created_at, datetime)

    def test_refresh_token_field_mutation(self, valid_refresh_token):
        valid_refresh_token.token_hash = "new_token_hash"
        assert valid_refresh_token.token_hash == "new_token_hash"

    def test_refresh_token_expires_after_created(self, valid_refresh_token):
        assert valid_refresh_token.created_at < valid_refresh_token.expires_at

    def test_refresh_token_different_user_ids_are_not_equal(self):
        t1 = RefreshToken(
            id=1,
            user_id=1,
            token_hash="hash",
            expires_at=LATER,
            revoked_at=None,
            remember_me=False,
            created_at=NOW,
        )
        t2 = RefreshToken(
            id=1,
            user_id=2,
            token_hash="hash",
            expires_at=LATER,
            revoked_at=None,
            remember_me=False,
            created_at=NOW,
        )
        assert t1 != t2
