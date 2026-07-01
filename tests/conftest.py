import os

# Doit s'executer AVANT tout import de app.config / app.database : Config lit
# les variables d'environnement au moment de l'import, et load_dotenv() ne
# remplace jamais une variable deja definie (override=False par defaut).
os.environ["DB_NAME"] = "easy_school_test_db"

import pytest

from app.database import init_db, create_tables, get_session, Base


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Cree les tables une fois pour toute la session de test."""
    engine = init_db()
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
