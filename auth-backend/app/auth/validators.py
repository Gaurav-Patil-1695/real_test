from __future__ import annotations

import re
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Password policy constants (mirrors capabilities.yaml)
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_NUMBER: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = False  # require_special_character = false

_UPPERCASE_RE = re.compile(r"[A-Z]")
_LOWERCASE_RE = re.compile(r"[a-z]")
_NUMBER_RE = re.compile(r"[0-9]")


# ---------------------------------------------------------------------------
# Low-level password policy checker
# Returns a list of validation error messages in the order specified by
# validation-rules.md.  An empty list means the password is valid.
# ---------------------------------------------------------------------------

def check_password_policy(password: str) -> list[str]:
    """Return ordered list of policy violation messages for *password*.

    Messages are copied VERBATIM from validation-rules.md.
    """
    errors: list[str] = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append("Password must be at least 8 characters.")

    if PASSWORD_REQUIRE_UPPERCASE and not _UPPERCASE_RE.search(password):
        errors.append("Password must contain at least one uppercase letter.")

    if PASSWORD_REQUIRE_LOWERCASE and not _LOWERCASE_RE.search(password):
        errors.append("Password must contain at least one lowercase letter.")

    if PASSWORD_REQUIRE_NUMBER and not _NUMBER_RE.search(password):
        errors.append("Password must contain at least one number.")

    return errors


# ---------------------------------------------------------------------------
# Field validators — used by Pydantic models (schemas.py) via validator()
# Each raises ValueError with the VERBATIM message from validation-rules.md.
# ---------------------------------------------------------------------------

def validate_full_name(value: str) -> str:
    """Full name must be non-empty and at most 255 characters."""
    value = value.strip()
    if not value:
        raise ValueError("Full name is required.")
    if len(value) > 255:
        raise ValueError("Full name must be at most 255 characters.")
    return value


def validate_email_field(value: str) -> str:
    """Email must be non-empty and syntactically valid."""
    value = value.strip().lower()
    if not value:
        raise ValueError("Email is required.")
    # Simple RFC-5321-aligned check; deep validation is done by Pydantic's EmailStr.
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Enter a valid email address.")
    return value


def validate_password_field(value: str) -> str:
    """Enforce the full password policy; raises ValueError on first batch of errors."""
    if not value:
        raise ValueError("Password is required.")
    errors = check_password_policy(value)
    if errors:
        # Raise with the first message; Pydantic surfaces each separately when
        # all rules are applied individually, but a single combined message is
        # acceptable per the spec (the frontend mirrors each rule individually).
        raise ValueError(errors[0])
    return value


def validate_confirm_password(password: str, confirm_password: str) -> str:
    """Confirm password must match password."""
    if confirm_password != password:
        raise ValueError("Passwords do not match.")
    return confirm_password


def validate_token_field(value: str) -> str:
    """Token must be non-empty."""
    value = value.strip()
    if not value:
        raise ValueError("Token is required.")
    return value


# ---------------------------------------------------------------------------
# Composite validator — used in the register / reset-password services to
# collect ALL field errors in one pass and return them as a structured dict.
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when one or more field-level validation errors are detected."""

    def __init__(self, field_errors: dict[str, list[str]]) -> None:
        super().__init__("Validation failed.")
        self.field_errors: dict[str, list[str]] = field_errors


def collect_password_policy_errors(password: str) -> list[str]:
    """Return ALL policy violation messages for *password* (used for rich UI feedback)."""
    return check_password_policy(password)


def validate_registration_fields(
    full_name: str,
    email: str,
    password: str,
    confirm_password: str,
) -> None:
    """Validate all registration fields; raise ValidationError if any fail.

    Validates fields in the order: full_name, email, password, confirm_password.
    Collects every error before raising so the caller gets a complete picture.
    """
    errors: dict[str, list[str]] = {}

    # full_name
    try:
        validate_full_name(full_name)
    except ValueError as exc:
        errors["full_name"] = [str(exc)]

    # email
    try:
        validate_email_field(email)
    except ValueError as exc:
        errors["email"] = [str(exc)]

    # password — collect ALL policy messages
    password_errors = collect_password_policy_errors(password) if password else ["Password is required."]
    if password_errors:
        errors["password"] = password_errors

    # confirm_password — only check if password itself is valid
    if not password_errors:
        try:
            validate_confirm_password(password, confirm_password)
        except ValueError as exc:
            errors["confirm_password"] = [str(exc)]

    if errors:
        raise ValidationError(errors)


def validate_reset_password_fields(
    password: str,
    confirm_password: str,
) -> None:
    """Validate password + confirm_password for the reset-password flow."""
    errors: dict[str, list[str]] = {}

    password_errors = collect_password_policy_errors(password) if password else ["Password is required."]
    if password_errors:
        errors["password"] = password_errors

    if not password_errors:
        try:
            validate_confirm_password(password, confirm_password)
        except ValueError as exc:
            errors["confirm_password"] = [str(exc)]

    if errors:
        raise ValidationError(errors)
