"""Test PostgreSQL autonome utilisé par l'installateur Easy School.

Les paramètres sensibles sont lus depuis un fichier temporaire créé par
l'installateur, jamais depuis la ligne de commande. Le résultat est écrit dans
un second fichier temporaire puis les deux fichiers sont supprimés par Inno
Setup immédiatement après le test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from psycopg2 import OperationalError


def _read_config(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")

    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lower()] = value
    return values


def _write_result(path: Path, message: str) -> None:
    # LoadStringFromFile d'Inno Setup lit un AnsiString. Windows-1252 permet
    # donc de conserver les accents français sans afficher un marqueur BOM.
    path.write_text(message, encoding="cp1252", errors="replace")


def _friendly_error(exc: OperationalError, host: str, port: int) -> tuple[int, str]:
    detail = str(exc).strip().replace("\r", " ").replace("\n", " ")
    lowered = detail.lower()
    if "password authentication failed" in lowered:
        return 2, "Authentification refusée : vérifiez l'utilisateur et le mot de passe PostgreSQL."
    if "does not exist" in lowered and "database" in lowered:
        return 2, "Base de données introuvable : vérifiez le nom de la base PostgreSQL."
    if any(marker in lowered for marker in ("timeout", "timed out", "connection refused", "could not connect")):
        return 3, f"Serveur PostgreSQL inaccessible sur {host}:{port}. Vérifiez l'adresse, le service et le pare-feu."
    return 4, f"Connexion PostgreSQL impossible : {detail}"


def main() -> int:
    if len(sys.argv) != 3:
        return 64

    config_path = Path(sys.argv[1])
    result_path = Path(sys.argv[2])
    try:
        config = _read_config(config_path)
        required = ("host", "port", "dbname", "user", "password")
        missing = [key for key in required if not config.get(key, "").strip()]
        if missing:
            _write_result(result_path, f"Paramètre obligatoire manquant : {', '.join(missing)}.")
            return 1

        try:
            port = int(config["port"])
        except ValueError:
            _write_result(result_path, "Le port PostgreSQL doit être un nombre entier.")
            return 1
        if not 1 <= port <= 65535:
            _write_result(result_path, "Le port PostgreSQL doit être compris entre 1 et 65535.")
            return 1

        try:
            connection = psycopg2.connect(
                host=config["host"].strip(),
                port=port,
                dbname=config["dbname"].strip(),
                user=config["user"].strip(),
                password=config["password"],
                connect_timeout=7,
                application_name="EasySchoolInstaller",
            )
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user, version()")
                    database, user, version = cursor.fetchone()
            finally:
                connection.close()
        except OperationalError as exc:
            code, message = _friendly_error(exc, config["host"].strip(), port)
            _write_result(result_path, message)
            return code

        postgres_version = str(version).split(",", 1)[0]
        _write_result(
            result_path,
            f"Connexion réussie à {postgres_version}. Base : {database}. Utilisateur : {user}.",
        )
        return 0
    except Exception as exc:
        try:
            _write_result(result_path, f"Test impossible : {exc}")
        except OSError:
            pass
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
