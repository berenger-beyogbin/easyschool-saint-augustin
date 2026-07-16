import os

# Doit s'executer AVANT tout import de app.config / app.database : Config lit
# les variables d'environnement au moment de l'import, et load_dotenv() ne
# remplace jamais une variable deja definie (override=False par defaut).
os.environ["DB_NAME"] = "easy_school_test_db"

import pytest
from sqlalchemy import text

from app.database import init_db, create_tables, get_session, Base


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Reconstruit le schema de test une fois pour toute la session.

    La base `easy_school_test_db` peut garder un ancien schema entre deux
    sessions pytest. `create_all()` n'altère pas les tables existantes ; on
    recharge donc les modèles via `create_tables()`, puis on supprime/recrée
    uniquement les tables de la base de test pour garantir un schema aligné
    sur les modèles courants.
    """
    engine = init_db()
    if os.environ.get("DB_NAME") != "easy_school_test_db":
        raise RuntimeError("Refus de reconstruire le schéma hors base de test.")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    create_tables()
    yield engine


@pytest.fixture(autouse=True)
def _clean_tables():
    """Vide les tables entre chaque test pour eviter les effets de bord."""
    yield
    session = get_session()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()
