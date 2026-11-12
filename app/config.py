import os
import sys
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env s'il existe
_runtime_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
load_dotenv(_runtime_dir / ".env")

class Config:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    # Base dediee a l'adaptation CJGA (College Catholique Joseph Garnier Attingue),
    # separee de la base historique du primaire pour eviter tout melange de donnees.
    DB_NAME = os.getenv("DB_NAME", "easy_school_cjga_db")

    # Flags de désactivation fonctionnelle pour la version college CJGA.
    # Masquage UI uniquement : aucune table/colonne n'est supprimee, les
    # anciennes structures (VersementScol.MontantCantine, etc.) restent intactes.
    ENABLE_TRANSPORT = False
    ENABLE_CANTINE = False
    ENABLE_BIBLIOTHEQUE = False

    @classmethod
    def get_db_url(cls):
        # Genere l'URL de connexion SQLAlchemy pour PostgreSQL
        return (
            f"postgresql://{quote_plus(cls.DB_USER)}:{quote_plus(cls.DB_PASSWORD)}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )
