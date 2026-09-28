from pathlib import Path

from app import logging_config


def test_log_dir_uses_local_app_data_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(logging_config.os, "name", "nt")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert logging_config._get_log_dir() == tmp_path / "EasySchool" / "logs"


def test_log_dir_has_a_user_fallback_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(logging_config.os, "name", "nt")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setattr(logging_config.pathlib.Path, "home", lambda: Path(tmp_path))

    assert logging_config._get_log_dir() == tmp_path / "AppData" / "Local" / "EasySchool" / "logs"
