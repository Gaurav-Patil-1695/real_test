import json
import pytest

from app.common.errors import (
    AppException,
    EmailTakenError,
    ErrorCode,
    InternalError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)
from app.common.responses import error_response, error_response_from_exception


# ---------------------------------------------------------------------------
# ErrorCode
# ---------------------------------------------------------------------------

class TestErrorCode:
    def test_all_members_are_strings(self):
        for member in ErrorCode:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self):
        expected = {
            "VALIDATION_ERROR",
            "INVALID_CREDENTIALS",
            "EMAIL_TAKEN",
            "INVALID_TOKEN",
            "UNAUTHORIZED",
            "RATE_LIMITED",
            "INTERNAL_ERROR",
        }
        assert {m.value for m in ErrorCode} == expected

    def test_error_code_is_str_subclass(self):
        assert issubclass(ErrorCode, str)


# ---------------------------------------------------------------------------
# AppException
# ---------------------------------------------------------------------------

class TestAppException:
    def test_basic_attributes(self):
        exc = AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="oops",
            status_code=500,
        )
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.message == "oops"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_default_status_code(self):
        exc = AppException(code=ErrorCode.VALIDATION_ERROR, message="bad")
        assert exc.status_code == 400

    def test_details_provided(self):
        details = {"field": "email", "reason": "required"}
        exc = AppException(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad",
            details=details,
        )
        assert exc.details == details

    def test_details_none_becomes_empty_dict(self):
        exc = AppException(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad",
            details=None,
        )
        assert exc.details == {}

    def test_is_exception(self):
        exc = AppException(code=ErrorCode.INTERNAL_ERROR, message="err")
        assert isinstance(exc, Exception)

    def test_str_representation(self):
        exc = AppException(code=ErrorCode.INTERNAL_ERROR, message="err msg")
        assert str(exc) == "err msg"

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AppException) as exc_info:
            raise AppException(
                code=ErrorCode.UNAUTHORIZED,
                message="not allowed",
                status_code=401,
            )
        assert exc_info.value.code == ErrorCode.UNAUTHORIZED


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------

class TestValidationError:
    def test_defaults(self):
        exc = ValidationError(message="invalid input")
        assert exc.code == ErrorCode.VALIDATION_ERROR
        assert exc.message == "invalid input"
        assert exc.status_code == 422
        assert exc.details == {}

    def test_with_details(self):
        details = {"field": "username"}
        exc = ValidationError(message="bad", details=details)
        assert exc.details == details

    def test_is_app_exception(self):
        assert isinstance(ValidationError("x"), AppException)

    def test_can_be_raised(self):
        with pytest.raises(ValidationError):
            raise ValidationError("oops")


# ---------------------------------------------------------------------------
# InvalidCredentialsError
# ---------------------------------------------------------------------------

class TestInvalidCredentialsError:
    def test_defaults(self):
        exc = InvalidCredentialsError()
        assert exc.code == ErrorCode.INVALID_CREDENTIALS
        assert exc.message == "Invalid email or password."
        assert exc.status_code == 401
        assert exc.details == {}

    def test_is_app_exception(self):
        assert isinstance(InvalidCredentialsError(), AppException)


# ---------------------------------------------------------------------------
# EmailTakenError
# ---------------------------------------------------------------------------

class TestEmailTakenError:
    def test_defaults(self):
        exc = EmailTakenError()
        assert exc.code == ErrorCode.EMAIL_TAKEN
        assert exc.message == "An account with this email already exists."
        assert exc.status_code == 409
        assert exc.details == {}

    def test_is_app_exception(self):
        assert isinstance(EmailTakenError(), AppException)


# ---------------------------------------------------------------------------
# InvalidTokenError
# ---------------------------------------------------------------------------

class TestInvalidTokenError:
    def test_defaults(self):
        exc = InvalidTokenError()
        assert exc.code == ErrorCode.INVALID_TOKEN
        assert exc.message == "Invalid or expired token."
        assert exc.status_code == 400
        assert exc.details == {}

    def test_custom_message(self):
        exc = InvalidTokenError(message="Token has expired.")
        assert exc.message == "Token has expired."

    def test_is_app_exception(self):
        assert isinstance(InvalidTokenError(), AppException)


# ---------------------------------------------------------------------------
# UnauthorizedError
# ---------------------------------------------------------------------------

class TestUnauthorizedError:
    def test_defaults(self):
        exc = UnauthorizedError()
        assert exc.code == ErrorCode.UNAUTHORIZED
        assert exc.message == "Authentication required."
        assert exc.status_code == 401
        assert exc.details == {}

    def test_custom_message(self):
        exc = UnauthorizedError(message="Go away.")
        assert exc.message == "Go away."

    def test_is_app_exception(self):
        assert isinstance(UnauthorizedError(), AppException)


# ---------------------------------------------------------------------------
# RateLimitedError
# ---------------------------------------------------------------------------

class TestRateLimitedError:
    def test_defaults(self):
        exc = RateLimitedError()
        assert exc.code == ErrorCode.RATE_LIMITED
        assert exc.message == "Too many requests. Please try again later."
        assert exc.status_code == 429
        assert exc.details == {}

    def test_custom_message(self):
        exc = RateLimitedError(message="Slow down!")
        assert exc.message == "Slow down!"

    def test_is_app_exception(self):
        assert isinstance(RateLimitedError(), AppException)


# ---------------------------------------------------------------------------
# InternalError
# ---------------------------------------------------------------------------

class TestInternalError:
    def test_defaults(self):
        exc = InternalError()
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.message == "An unexpected error occurred."
        assert exc.status_code == 500
        assert exc.details == {}

    def test_custom_message(self):
        exc = InternalError(message="DB is down.")
        assert exc.message == "DB is down."

    def test_is_app_exception(self):
        assert isinstance(InternalError(), AppException)


# ---------------------------------------------------------------------------
# error_response
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def _parse_body(self, response):
        """Return the parsed JSON body of a JSONResponse."""
        return json.loads(response.body)

    def test_status_code(self):
        resp = error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="not allowed",
            status_code=401,
        )
        assert resp.status_code == 401

    def test_body_structure(self):
        resp = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad input",
            status_code=422,
        )
        body = self._parse_body(resp)
        assert "error" in body
        error = body["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["message"] == "bad input"
        assert error["details"] == {}

    def test_with_details(self):
        details = {"field": "email"}
        resp = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad",
            status_code=422,
            details=details,
        )
        body = self._parse_body(resp)
        assert body["error"]["details"] == details

    def test_details_none_becomes_empty_dict(self):
        resp = error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="err",
            status_code=500,
            details=None,
        )
        body = self._parse_body(resp)
        assert body["error"]["details"] == {}

    def test_default_status_code(self):
        resp = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="bad",
        )
        assert resp.status_code == 400

    def test_code_value_in_body(self):
        resp = error_response(
            code=ErrorCode.RATE_LIMITED,
            message="slow down",
            status_code=429,
        )
        body = self._parse_body(resp)
        assert body["error"]["code"] == "RATE_LIMITED"


# ---------------------------------------------------------------------------
# error_response_from_exception
# ---------------------------------------------------------------------------

class TestErrorResponseFromException:
    def _parse_body(self, response):
        return json.loads(response.body)

    def test_validation_error(self):
        exc = ValidationError(message="bad field", details={"field": "name"})
        resp = error_response_from_exception(exc)
        assert resp.status_code == 422
        body = self._parse_body(resp)
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "bad field"
        assert body["error"]["details"] == {"field": "name"}

    def test_invalid_credentials_error(self):
        exc = InvalidCredentialsError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 401
        body = self._parse_body(resp)
        assert body["error"]["code"] == "INVALID_CREDENTIALS"
        assert body["error"]["message"] == "Invalid email or password."

    def test_email_taken_error(self):
        exc = EmailTakenError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 409
        body = self._parse_body(resp)
        assert body["error"]["code"] == "EMAIL_TAKEN"

    def test_invalid_token_error_default(self):
        exc = InvalidTokenError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 400
        body = self._parse_body(resp)
        assert body["error"]["code"] == "INVALID_TOKEN"
        assert body["error"]["message"] == "Invalid or expired token."

    def test_invalid_token_error_custom_message(self):
        exc = InvalidTokenError(message="Token expired.")
        resp = error_response_from_exception(exc)
        body = self._parse_body(resp)
        assert body["error"]["message"] == "Token expired."

    def test_unauthorized_error(self):
        exc = UnauthorizedError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 401
        body = self._parse_body(resp)
        assert body["error"]["code"] == "UNAUTHORIZED"

    def test_rate_limited_error(self):
        exc = RateLimitedError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 429
        body = self._parse_body(resp)
        assert body["error"]["code"] == "RATE_LIMITED"

    def test_internal_error(self):
        exc = InternalError()
        resp = error_response_from_exception(exc)
        assert resp.status_code == 500
        body = self._parse_body(resp)
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_details_propagated(self):
        exc = ValidationError(message="err", details={"a": 1, "b": "two"})
        resp = error_response_from_exception(exc)
        body = self._parse_body(resp)
        assert body["error"]["details"] == {"a": 1, "b": "two"}

    def test_empty_details_propagated(self):
        exc = UnauthorizedError()
        resp = error_response_from_exception(exc)
        body = self._parse_body(resp)
        assert body["error"]["details"] == {}

    def test_generic_app_exception(self):
        exc = AppException(
            code=ErrorCode.INTERNAL_ERROR,
            message="custom msg",
            status_code=503,
            details={"reason": "overload"},
        )
        resp = error_response_from_exception(exc)
        assert resp.status_code == 503
        body = self._parse_body(resp)
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "custom msg"
        assert body["error"]["details"] == {"reason": "overload"}
