from pathlib import Path
from types import SimpleNamespace

import pytest

from services import backup_service


def _redirect_app_data(monkeypatch, tmp_path):
    monkeypatch.setattr(backup_service, "get_app_data_dir", lambda: tmp_path / "appdata")


def test_settings_round_trip(monkeypatch, tmp_path):
    _redirect_app_data(monkeypatch, tmp_path)
    backup_dir = tmp_path / "copies"
    settings = backup_service.BackupSettings(str(backup_dir), True, "21:30", 7)

    backup_service.save_settings(settings)

    assert backup_service.load_settings() == settings


def test_run_backup_validates_backup_then_rotates(monkeypatch, tmp_path):
    _redirect_app_data(monkeypatch, tmp_path)
    backup_dir = tmp_path / "copies"
    backup_dir.mkdir()
    for index in range(3):
        old = backup_dir / f"easy_school_easy_school_test_db2_2026-01-0{index + 1}_200000.backup"
        old.write_bytes(b"old")

    fake_pg_dump = tmp_path / "pg_dump.exe"
    fake_pg_dump.write_bytes(b"exe")
    monkeypatch.setattr(backup_service, "find_pg_dump", lambda: fake_pg_dump)

    def fake_run(command, **kwargs):
        partial = Path(command[command.index("--file") + 1])
        partial.write_bytes(b"valid-backup")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(backup_service.subprocess, "run", fake_run)
    settings = backup_service.BackupSettings(str(backup_dir), False, "20:00", 2)

    result = backup_service.run_backup(settings)

    assert Path(result.file_path).suffix == ".backup"
    assert Path(result.file_path).read_bytes() == b"valid-backup"
    assert len(list(backup_dir.glob("*.backup"))) == 2
    assert not list(backup_dir.glob("*.partial"))
    assert backup_service.load_status()["success"] is True


def test_failed_backup_is_not_kept(monkeypatch, tmp_path):
    _redirect_app_data(monkeypatch, tmp_path)
    backup_dir = tmp_path / "copies"
    fake_pg_dump = tmp_path / "pg_dump.exe"
    fake_pg_dump.write_bytes(b"exe")
    monkeypatch.setattr(backup_service, "find_pg_dump", lambda: fake_pg_dump)
    monkeypatch.setattr(
        backup_service.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="connexion refusée"),
    )

    with pytest.raises(backup_service.BackupError, match="connexion refusée"):
        backup_service.run_backup(backup_service.BackupSettings(str(backup_dir), False, "20:00", 14))

    assert not list(backup_dir.glob("*.backup"))
    assert not list(backup_dir.glob("*.partial"))
    assert backup_service.load_status()["success"] is False


def test_registers_daily_windows_task(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(backup_service.os, "name", "nt")
    monkeypatch.setattr(
        backup_service.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command) or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    settings = backup_service.BackupSettings(str(tmp_path), True, "22:15", 14)

    backup_service.register_scheduled_task(settings)

    command = calls[0]
    assert command[:3] == ["schtasks.exe", "/Create", "/F"]
    assert command[command.index("/SC") + 1] == "DAILY"
    assert command[command.index("/ST") + 1] == "22:15"
    assert command[command.index("/TR") + 1].endswith("--backup-now")
