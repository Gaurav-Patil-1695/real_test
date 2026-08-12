"""Unit tests for app.db.database module."""
from collections.abc import Generator
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    """Provide a fake DATABASE_URL so no real DB is required."""
    fake_settings = MagicMock()
    fake_settings.DATABASE_URL = "sqlite:///:memory:"
    monkeypatch.setattr("app.config.settings.settings", fake_settings)
    return fake_settings


# We import the module under test AFTER patching settings so the engine is
# created with the fake URL.  Use importlib to force a fresh import each time.
import importlib
import sys


@pytest.fixture()
def db_module():
    """Return a freshly-imported copy of app.db.database."""
    # Remove any cached module so settings patch takes effect
    for key in list(sys.modules.keys()):
        if "app.db.database" in key:
            del sys.modules[key]
    import app.db.database as mod
    return mod


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------

class TestEngine:
    def test_engine_is_created(self, db_module):
        """engine should be a SQLAlchemy Engine instance."""
        from sqlalchemy.engine import Engine
        assert isinstance(db_module.engine, Engine)

    def test_engine_uses_configured_url(self, db_module):
        """engine URL must match the value from settings."""
        # sqlite:///:memory: -> dialect is sqlite
        assert db_module.engine.dialect.name == "sqlite"


# ---------------------------------------------------------------------------
# SessionLocal
# ---------------------------------------------------------------------------

class TestSessionLocal:
    def test_session_local_is_sessionmaker(self, db_module):
        """SessionLocal should be a sessionmaker factory."""
        from sqlalchemy.orm import sessionmaker
        assert isinstance(db_module.SessionLocal, sessionmaker)

    def test_session_local_autocommit_false(self, db_module):
        assert db_module.SessionLocal.kw.get("autocommit", False) is False

    def test_session_local_autoflush_false(self, db_module):
        assert db_module.SessionLocal.kw.get("autoflush", True) is False

    def test_session_local_bound_to_engine(self, db_module):
        """SessionLocal must be bound to the module-level engine."""
        assert db_module.SessionLocal.kw.get("bind") is db_module.engine


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class TestBase:
    def test_base_is_declarative(self, db_module):
        """Base should be a DeclarativeBase subclass."""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(db_module.Base, DeclarativeBase)

    def test_base_has_metadata(self, db_module):
        from sqlalchemy import MetaData
        assert isinstance(db_module.Base.metadata, MetaData)


# ---------------------------------------------------------------------------
# get_db
# ---------------------------------------------------------------------------

class TestGetDb:
    def test_get_db_is_generator_function(self, db_module):
        """get_db should return a generator when called."""
        gen = db_module.get_db()
        assert isinstance(gen, Generator)
        # Clean up
        gen.close()

    def test_get_db_yields_a_session(self, db_module):
        """get_db should yield exactly one Session object."""
        from sqlalchemy.orm import Session
        gen = db_module.get_db()
        session = next(gen)
        assert isinstance(session, Session)
        # Exhaust / close generator
        gen.close()

    def test_get_db_closes_session_on_normal_exit(self, db_module):
        """Session.close() must be called after the generator is exhausted."""
        sessions_created = []

        original_session_local = db_module.SessionLocal

        def fake_session_local():
            mock_session = MagicMock()
            sessions_created.append(mock_session)
            return mock_session

        with patch.object(db_module, "SessionLocal", side_effect=fake_session_local):
            gen = db_module.get_db()
            session = next(gen)
            # Simulate the caller finishing normally
            with pytest.raises(StopIteration):
                next(gen)

        assert len(sessions_created) == 1
        sessions_created[0].close.assert_called_once()

    def test_get_db_closes_session_on_exception(self, db_module):
        """Session.close() must be called even when an exception is thrown into the generator."""
        mock_session = MagicMock()

        with patch.object(db_module, "SessionLocal", return_value=mock_session):
            gen = db_module.get_db()
            next(gen)  # obtain session
            with pytest.raises(RuntimeError):
                gen.throw(RuntimeError, RuntimeError("boom"))

        mock_session.close.assert_called_once()

    def test_get_db_yields_only_once(self, db_module):
        """get_db must yield exactly one value (the session)."""
        mock_session = MagicMock()

        with patch.object(db_module, "SessionLocal", return_value=mock_session):
            gen = db_module.get_db()
            first = next(gen)
            assert first is mock_session
            with pytest.raises(StopIteration):
                next(gen)

    def test_get_db_creates_new_session_each_call(self, db_module):
        """Each call to get_db() should produce an independent session."""
        sessions = []

        def factory():
            s = MagicMock()
            sessions.append(s)
            return s

        with patch.object(db_module, "SessionLocal", side_effect=factory):
            gen1 = db_module.get_db()
            gen2 = db_module.get_db()
            s1 = next(gen1)
            s2 = next(gen2)
            gen1.close()
            gen2.close()

        assert s1 is not s2
        assert len(sessions) == 2
