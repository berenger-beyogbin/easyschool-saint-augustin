import pytest

from app import database


def _record_startup_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(database, "init_db", lambda: calls.append("init"))
    monkeypatch.setattr(database, "test_connection", lambda: calls.append("connection"))
    monkeypatch.setattr(database, "create_tables", lambda: calls.append("create_tables"))
    return calls


def test_production_startup_only_checks_connection(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    calls = _record_startup_calls(monkeypatch)

    mode = database.prepare_database_for_startup()

    assert mode == "connection_only"
    assert calls == ["init", "connection"]


@pytest.mark.parametrize("app_env", ["dev", "dev_debug", "test"])
def test_local_startup_keeps_automatic_schema_creation(monkeypatch, app_env):
    monkeypatch.setenv("APP_ENV", app_env)
    calls = _record_startup_calls(monkeypatch)

    mode = database.prepare_database_for_startup()

    assert mode == "local_schema_created"
    assert calls == ["init", "connection", "create_tables"]


def test_missing_environment_defaults_to_safe_production_behavior(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    calls = _record_startup_calls(monkeypatch)

    mode = database.prepare_database_for_startup()

    assert mode == "connection_only"
    assert calls == ["init", "connection"]


def test_unknown_environment_stops_before_touching_database(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    calls = _record_startup_calls(monkeypatch)

    with pytest.raises(RuntimeError, match="APP_ENV invalide"):
        database.prepare_database_for_startup()

    assert calls == []
