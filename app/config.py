import os
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env s'il existe
load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    # Base dediee a l'adaptation CJGA (College Catholique Joseph Garnier Attingue),
    # separee de la base historique du primaire pour eviter tout melange de donnees.
    DB_NAME = os.getenv("DB_NAME", "easy_school_csja_db")

    @classmethod
    def get_db_url(cls):
        # Genere l'URL de connexion SQLAlchemy pour PostgreSQL
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
