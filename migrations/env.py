import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Permet d'importer app/, models/, services/ depuis migrations/env.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.database import Base

# Importe tous les modeles pour que Base.metadata les connaisse avant tout
# autogenerate (meme liste que app.database.create_tables()).
import models.etablissement  # noqa: E402,F401
import models.annee_scolaire  # noqa: E402,F401
import models.cycle  # noqa: E402,F401
import models.niveau  # noqa: E402,F401
import models.classe  # noqa: E402,F401
import models.nationalite  # noqa: E402,F401
import models.religion  # noqa: E402,F401
import models.famille  # noqa: E402,F401
import models.eleve  # noqa: E402,F401
import models.inscription  # noqa: E402,F401
import models.autres_frais  # noqa: E402,F401
import models.montant_autres_frais  # noqa: E402,F401
import models.inscription_autres_frais  # noqa: E402,F401
import models.montant_scol  # noqa: E402,F401
import models.montant_cantine  # noqa: E402,F401
import models.montant_transport  # noqa: E402,F401
import models.versement_scol  # noqa: E402,F401
import models.versement_autres_frais  # noqa: E402,F401
import models.article  # noqa: E402,F401
import models.stock_cour  # noqa: E402,F401
import models.stock_entree  # noqa: E402,F401
import models.stock_sortie  # noqa: E402,F401
import models.compte  # noqa: E402,F401
import models.type_sortie  # noqa: E402,F401
import models.sortie_fin  # noqa: E402,F401
import models.profil  # noqa: E402,F401
import models.permission  # noqa: E402,F401
import models.profil_permission  # noqa: E402,F401
import models.utilisateur  # noqa: E402,F401
import models.audit_log  # noqa: E402,F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Injecte l'URL de connexion depuis .env (via Config), jamais depuis alembic.ini
config.set_main_option("sqlalchemy.url", Config.get_db_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Tables retirees du code lors de l'adaptation CJGA, mais conservees en base
# pour eviter tout DROP TABLE destructif sur des installations existantes.
LEGACY_RETAINED_TABLES = {
    "Prestataire",
    "PrestationAnnexe",
    "VentilationPrestation",
}


def include_object(object_, name, type_, reflected, compare_to):
    """Exclut les tables legacy conservees de l'autogeneration Alembic."""
    if type_ == "table" and reflected and compare_to is None and name in LEGACY_RETAINED_TABLES:
        return False
    if type_ == "index" and reflected and getattr(object_, "table", None) is not None:
        if object_.table.name in LEGACY_RETAINED_TABLES:
            return False
    return True

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
