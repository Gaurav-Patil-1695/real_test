"""Unit tests for app.auth.validators."""
from __future__ import annotations

import pytest

from app.auth.validators import (
    check_password_policy,
    validate_full_name,
    validate_email_field,
    validate_password_field,
    validate_confirm_password,
    validate_token_field,
    collect_password_policy_errors,
    validate_registration_fields,
    validate_reset_password_fields,
    ValidationError,
    PASSWORD_MIN_LENGTH,
)


# ===========================================================================
# check_password_policy
# ===========================================================================

class TestCheckPasswordPolicy:
    def test_valid_password_returns_empty_list(self):
        assert check_password_policy("Password1") == []

    def test_too_short(self):
        errors = check_password_policy("Pa1")
        assert any("8 characters" in e for e in errors)

    def test_missing_uppercase(self):
        errors = check_password_policy("password1")
        assert any("uppercase" in e for e in errors)

    def test_missing_lowercase(self):
        errors = check_password_policy("PASSWORD1")
        assert any("lowercase" in e for e in errors)

    def test_missing_number(self):
        errors = check_password_policy("Password")
        assert any("number" in e for e in errors)

    def test_multiple_violations_all_reported(self):
        # All lowercase short password with no number
        errors = check_password_policy("ab")
        assert len(errors) >= 3  # too short, no uppercase, no number

    def test_exactly_min_length_valid(self):
        # Exactly 8 chars with all required categories
        assert check_password_policy("Abcdef1g") == []

    def test_error_ordering(self):
        # Short + no uppercase + no number → length error comes first
        errors = check_password_policy("abc")
        assert "8 characters" in errors[0]


# ===========================================================================
# validate_full_name
# ===========================================================================

class TestValidateFullName:
    def test_valid_name_returned_stripped(self):
        assert validate_full_name("  Alice  ") == "Alice"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Full name is required"):
            validate_full_name("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Full name is required"):
            validate_full_name("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="255 characters"):
            validate_full_name("A" * 256)

    def test_exactly_255_allowed(self):
        name = "A" * 255
        assert validate_full_name(name) == name


# ===========================================================================
# validate_email_field
# ===========================================================================

class TestValidateEmailField:
    def test_valid_email_lowercased(self):
        assert validate_email_field("Alice@Example.COM") == "alice@example.com"

    def test_valid_email_stripped(self):
        assert validate_email_field("  user@domain.com  ") == "user@domain.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Email is required"):
            validate_email_field("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Email is required"):
            validate_email_field("   ")

    def test_missing_at_raises(self):
        with pytest.raises(ValueError, match="valid email"):
            validate_email_field("nodomain")

    def test_starts_with_at_raises(self):
        with pytest.raises(ValueError, match="valid email"):
            validate_email_field("@domain.com")

    def test_ends_with_at_raises(self):
        with pytest.raises(ValueError, match="valid email"):
            validate_email_field("user@")


# ===========================================================================
# validate_password_field
# ===========================================================================

class TestValidatePasswordField:
    def test_valid_password_returned(self):
        assert validate_password_field("Secure99") == "Secure99"

    def test_empty_raises_required(self):
        with pytest.raises(ValueError, match="Password is required"):
            validate_password_field("")

    def test_policy_violation_raises(self):
        with pytest.raises(ValueError):
            validate_password_field("short")

    def test_no_uppercase_raises(self):
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_field("password1")

    def test_no_number_raises(self):
        with pytest.raises(ValueError, match="number"):
            validate_password_field("Password")


# ===========================================================================
# validate_confirm_password
# ===========================================================================

class TestValidateConfirmPassword:
    def test_matching_returns_confirm(self):
        assert validate_confirm_password("abc", "abc") == "abc"

    def test_mismatch_raises(self):
        with pytest.raises(ValueError, match="do not match"):
            validate_confirm_password("abc", "xyz")

    def test_empty_strings_match(self):
        assert validate_confirm_password("", "") == ""


# ===========================================================================
# validate_token_field
# ===========================================================================

class TestValidateTokenField:
    def test_valid_token_stripped(self):
        assert validate_token_field("  mytoken  ") == "mytoken"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Token is required"):
            validate_token_field("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Token is required"):
            validate_token_field("   ")


# ===========================================================================
# collect_password_policy_errors
# ===========================================================================

class TestCollectPasswordPolicyErrors:
    def test_valid_password_empty_list(self):
        assert collect_password_policy_errors("Password1") == []

    def test_collects_all_errors(self):
        # "ab" → too short, no uppercase, no number
        errors = collect_password_policy_errors("ab")
        assert len(errors) >= 3


# ===========================================================================
# ValidationError
# ===========================================================================

class TestValidationError:
    def test_stores_field_errors(self):
        err = ValidationError({"email": ["Email is required."]})
        assert err.field_errors == {"email": ["Email is required."]}

    def test_is_exception(self):
        err = ValidationError({})
        assert isinstance(err, Exception)


# ===========================================================================
# validate_registration_fields
# ===========================================================================

class TestValidateRegistrationFields:
    def test_valid_fields_passes(self):
        # Should not raise
        validate_registration_fields("Alice Smith", "alice@example.com",
                                     "Password1", "Password1")

    def test_empty_full_name_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("", "alice@example.com",
                                         "Password1", "Password1")
        assert "full_name" in exc_info.value.field_errors

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("Alice", "bademail",
                                         "Password1", "Password1")
        assert "email" in exc_info.value.field_errors

    def test_empty_password_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("Alice", "alice@example.com", "", "")
        assert "password" in exc_info.value.field_errors
        assert exc_info.value.field_errors["password"] == ["Password is required."]

    def test_weak_password_collects_all_errors(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("Alice", "alice@example.com", "ab", "ab")
        assert "password" in exc_info.value.field_errors
        assert len(exc_info.value.field_errors["password"]) >= 2

    def test_mismatched_confirm_password_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("Alice", "alice@example.com",
                                         "Password1", "Wrong1")
        assert "confirm_password" in exc_info.value.field_errors

    def test_confirm_password_not_checked_when_password_invalid(self):
        # When password is invalid, confirm_password errors should not appear
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("Alice", "alice@example.com",
                                         "weak", "different")
        assert "confirm_password" not in exc_info.value.field_errors

    def test_multiple_field_errors_collected(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_registration_fields("", "bademail", "", "")
        errors = exc_info.value.field_errors
        assert "full_name" in errors
        assert "email" in errors
        assert "password" in errors


# ===========================================================================
# validate_reset_password_fields
# ===========================================================================

class TestValidateResetPasswordFields:
    def test_valid_fields_passes(self):
        validate_reset_password_fields("Password1", "Password1")

    def test_empty_password_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_reset_password_fields("", "")
        assert "password" in exc_info.value.field_errors
        assert exc_info.value.field_errors["password"] == ["Password is required."]

    def test_weak_password_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_reset_password_fields("abc", "abc")
        assert "password" in exc_info.value.field_errors

    def test_mismatched_confirm_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_reset_password_fields("Password1", "Password2")
        assert "confirm_password" in exc_info.value.field_errors

    def test_confirm_not_checked_when_password_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_reset_password_fields("weak", "different")
        assert "confirm_password" not in exc_info.value.field_errors
