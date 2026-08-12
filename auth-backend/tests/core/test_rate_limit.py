"""Unit tests for app.core.rate_limit."""

from slowapi import Limiter

from app.core.rate_limit import FORGOT_PASSWORD_LIMIT, LOGIN_LIMIT, limiter
from app.config.settings import settings


class TestLimiterInstance:
    def test_limiter_is_limiter_instance(self):
        assert isinstance(limiter, Limiter)

    def test_limiter_has_no_default_limits(self):
        # The limiter is configured with default_limits=[]
        assert limiter._default_limits == [] or limiter.default_limits == []


class TestLimitStrings:
    def test_login_limit_is_string(self):
        assert isinstance(LOGIN_LIMIT, str)
        assert len(LOGIN_LIMIT) > 0

    def test_forgot_password_limit_is_string(self):
        assert isinstance(FORGOT_PASSWORD_LIMIT, str)
        assert len(FORGOT_PASSWORD_LIMIT) > 0

    def test_login_limit_matches_settings(self):
        assert LOGIN_LIMIT == settings.LOGIN_RATE_LIMIT

    def test_forgot_password_limit_matches_settings(self):
        assert FORGOT_PASSWORD_LIMIT == settings.FORGOT_PASSWORD_RATE_LIMIT
