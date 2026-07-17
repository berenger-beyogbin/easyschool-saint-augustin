import logging
import logging.handlers
import os
import pathlib

_LOG_DIR = pathlib.Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "easy_school.log"

_configured = False


def setup_logging() -> None:
    """Configure le logging applicatif une seule fois, au demarrage.

    Fichier journal avec rotation (5 Mo x 5 fichiers) + console. Remplace les
    print() de diagnostic disperses dans les services (audit P1-10) : chaque
    entree porte desormais un horodatage, un niveau et le module d'origine,
    et les exceptions capturees incluent la trace complete.
    """
    global _configured
    if _configured:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    app_env = os.environ.get("APP_ENV", "dev")
    level = logging.DEBUG if app_env == "dev_debug" else logging.INFO

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True
