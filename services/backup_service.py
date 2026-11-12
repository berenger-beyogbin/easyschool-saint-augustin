"""Sauvegarde PostgreSQL et planification Windows pour Easy School."""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from app.config import Config


logger = logging.getLogger(__name__)

TASK_NAME = "EasySchool - Sauvegarde quotidienne"
SETTINGS_FILENAME = "backup_settings.json"
STATUS_FILENAME = "backup_status.json"
LOCK_FILENAME = "backup.lock"
BACKUP_EXTENSION = ".backup"


class BackupError(RuntimeError):
    """Erreur fonctionnelle affichable dans l'interface utilisateur."""


@dataclass
class BackupSettings:
    backup_dir: str = ""
    enabled: bool = False
    schedule_time: str = "20:00"
    keep_last: int = 14


@dataclass
class BackupResult:
    file_path: str
    size_bytes: int
    completed_at: str


def get_app_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "EasySchool"


def _json_path(filename: str) -> Path:
    return get_app_data_dir() / filename


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp_path, path)


def load_settings() -> BackupSettings:
    path = _json_path(SETTINGS_FILENAME)
    if not path.exists():
        return BackupSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        settings = BackupSettings(
            backup_dir=str(raw.get("backup_dir", "")),
            enabled=bool(raw.get("enabled", False)),
            schedule_time=str(raw.get("schedule_time", "20:00")),
            keep_last=int(raw.get("keep_last", 14)),
        )
        validate_settings(settings, require_directory=False)
        return settings
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("Configuration de sauvegarde invalide, valeurs par defaut utilisees : %s", exc)
        return BackupSettings()


def save_settings(settings: BackupSettings) -> None:
    validate_settings(settings, require_directory=True)
    _write_json_atomic(_json_path(SETTINGS_FILENAME), asdict(settings))


def load_status() -> dict:
    path = _json_path(STATUS_FILENAME)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def validate_settings(settings: BackupSettings, *, require_directory: bool = True) -> None:
    if require_directory and not settings.backup_dir.strip():
        raise BackupError("Choisissez d'abord un dossier de sauvegarde.")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", settings.schedule_time):
        raise BackupError("L'heure de sauvegarde est invalide.")
    if not 1 <= settings.keep_last <= 365:
        raise BackupError("Le nombre de sauvegardes à conserver doit être compris entre 1 et 365.")


def find_pg_dump() -> Path | None:
    configured = os.environ.get("PG_DUMP_PATH", "").strip()
    if configured and Path(configured).is_file():
        return Path(configured)

    candidates: list[Path] = []
    runtime_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
    for bundled in (runtime_dir / "postgresql" / "pg_dump.exe", runtime_dir / "pg_dump.exe"):
        if bundled.is_file():
            candidates.append(bundled)

    on_path = shutil.which("pg_dump")
    if on_path:
        candidates.append(Path(on_path))

    if os.name == "nt":
        postgres_roots: list[Path] = []
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(env_name)
            if not root:
                continue
            postgres_roots.append(Path(root) / "PostgreSQL")
        system_drive = os.environ.get("SystemDrive", "C:")
        postgres_roots.append(Path(f"{system_drive}\\PostgreSQL"))

        for postgres_root in postgres_roots:
            if postgres_root.exists():
                candidates.extend(postgres_root.glob("*/bin/pg_dump.exe"))
                candidates.extend(postgres_root.glob("*/pgAdmin 4/runtime/pg_dump.exe"))
    if not candidates:
        return None

    unique_candidates = list(dict.fromkeys(path.resolve() for path in candidates))

    def version_key(item: Path) -> tuple[int, str]:
        try:
            completed = subprocess.run(
                [str(item), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
            match = re.search(r"PostgreSQL\)\s+(\d+)", completed.stdout or completed.stderr)
            major = int(match.group(1)) if match else 0
        except (OSError, subprocess.SubprocessError, ValueError):
            major = 0
        return major, str(item)

    return max(unique_candidates, key=version_key)


def _append_log(backup_dir: Path, completed_at: str, file_path: str, size_bytes: int, status: str) -> None:
    log_path = backup_dir / "backup_log.csv"
    new_file = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        if new_file:
            writer.writerow(["date", "base", "fichier", "taille_octets", "statut"])
        writer.writerow([completed_at, Config.DB_NAME, file_path, size_bytes, status])


def _record_status(*, success: bool, message: str, file_path: str = "", size_bytes: int = 0) -> None:
    _write_json_atomic(
        _json_path(STATUS_FILENAME),
        {
            "success": success,
            "message": message,
            "file_path": file_path,
            "size_bytes": size_bytes,
            "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    )


def _rotate_backups(backup_dir: Path, prefix: str, keep_last: int) -> None:
    backups = sorted(
        backup_dir.glob(f"{prefix}_*{BACKUP_EXTENSION}"),
        # Le nom contient yyyy-MM-dd_HHmmss : il donne un ordre fiable même
        # sur les volumes dont la précision d'horodatage est faible.
        key=lambda item: item.name,
        reverse=True,
    )
    for old_file in backups[keep_last:]:
        try:
            old_file.unlink()
            logger.info("Ancienne sauvegarde supprimee par rotation : %s", old_file)
        except OSError:
            logger.exception("Impossible de supprimer l'ancienne sauvegarde %s", old_file)


def _acquire_lock() -> tuple[int, Path]:
    lock_path = _json_path(LOCK_FILENAME)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        try:
            age_seconds = datetime.now().timestamp() - lock_path.stat().st_mtime
            if age_seconds > 12 * 60 * 60:
                lock_path.unlink()
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise BackupError("Une sauvegarde est déjà en cours.") from exc
        except FileNotFoundError:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(descriptor, str(os.getpid()).encode("ascii"))
    return descriptor, lock_path


def run_backup(settings: BackupSettings | None = None) -> BackupResult:
    settings = settings or load_settings()
    validate_settings(settings, require_directory=True)
    pg_dump = find_pg_dump()
    if pg_dump is None:
        message = (
            "L'outil pg_dump est introuvable. Installez les outils client PostgreSQL "
            "ou définissez PG_DUMP_PATH."
        )
        _record_status(success=False, message=message)
        raise BackupError(message)

    backup_dir = Path(settings.backup_dir).expanduser()
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BackupError(f"Impossible de créer le dossier de sauvegarde : {exc}") from exc

    descriptor, lock_path = _acquire_lock()
    safe_db_name = re.sub(r"[^A-Za-z0-9_.-]", "_", Config.DB_NAME)
    prefix = f"easy_school_{safe_db_name}"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    final_path = backup_dir / f"{prefix}_{timestamp}{BACKUP_EXTENSION}"
    partial_path = final_path.with_suffix(f"{BACKUP_EXTENSION}.partial")
    completed_at = datetime.now().astimezone().isoformat(timespec="seconds")

    env = os.environ.copy()
    env["PGPASSWORD"] = Config.DB_PASSWORD
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    command = [
        str(pg_dump),
        "--host", Config.DB_HOST,
        "--port", str(Config.DB_PORT),
        "--username", Config.DB_USER,
        "--dbname", Config.DB_NAME,
        "--format", "custom",
        "--file", str(partial_path),
    ]

    try:
        completed = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=60 * 60,
            creationflags=creation_flags,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "Erreur inconnue").strip()
            raise BackupError(f"La sauvegarde PostgreSQL a échoué : {detail}")
        if not partial_path.exists() or partial_path.stat().st_size == 0:
            raise BackupError("La sauvegarde produite est vide.")

        os.replace(partial_path, final_path)
        size_bytes = final_path.stat().st_size
        _append_log(backup_dir, completed_at, str(final_path), size_bytes, "OK")
        _rotate_backups(backup_dir, prefix, settings.keep_last)
        _record_status(
            success=True,
            message="Sauvegarde terminée avec succès.",
            file_path=str(final_path),
            size_bytes=size_bytes,
        )
        logger.info("Sauvegarde terminee : %s (%s octets)", final_path, size_bytes)
        return BackupResult(str(final_path), size_bytes, completed_at)
    except (OSError, subprocess.SubprocessError, BackupError) as exc:
        partial_path.unlink(missing_ok=True)
        message = str(exc)
        try:
            _append_log(backup_dir, completed_at, str(final_path), 0, f"ECHEC: {message}")
        except OSError:
            logger.exception("Impossible d'ecrire le journal de sauvegarde")
        _record_status(success=False, message=message)
        logger.exception("Echec de la sauvegarde")
        if isinstance(exc, BackupError):
            raise
        raise BackupError(message) from exc
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _scheduled_command() -> str:
    if getattr(sys, "frozen", False):
        parts = [str(Path(sys.executable).resolve()), "--backup-now"]
    else:
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        parts = [str(Path(sys.executable).resolve()), str(main_path), "--backup-now"]
    return " ".join(f'"{part}"' if " " in part else part for part in parts)


def register_scheduled_task(settings: BackupSettings) -> None:
    validate_settings(settings, require_directory=True)
    if os.name != "nt":
        raise BackupError("La planification automatique est disponible uniquement sous Windows.")
    command = [
        "schtasks.exe", "/Create", "/F",
        "/TN", TASK_NAME,
        "/SC", "DAILY",
        "/ST", settings.schedule_time,
        "/TR", _scheduled_command(),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "Erreur inconnue").strip()
        raise BackupError(f"Impossible de créer la tâche Windows : {detail}")


def delete_scheduled_task() -> None:
    if os.name != "nt":
        return
    completed = subprocess.run(
        ["schtasks.exe", "/Delete", "/F", "/TN", TASK_NAME],
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    # Une tâche absente n'est pas une erreur bloquante.
    if completed.returncode != 0:
        logger.info("Tache de sauvegarde absente ou non supprimable : %s", (completed.stderr or completed.stdout).strip())
