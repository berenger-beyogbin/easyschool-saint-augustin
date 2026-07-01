import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import Config

# Base declarative pour tous les modeles SQLAlchemy
Base = declarative_base()

# Variables globales pour la session et l'moteur de base de donnees
_engine = None
_SessionLocal = None

def init_db():
    """Initialise le moteur SQLAlchemy et cree la session locale."""
    global _engine, _SessionLocal
    db_url = Config.get_db_url()

    # echo=True uniquement en mode dev_debug — évite de flooder la console en prod.
    # Configurer APP_ENV=dev_debug dans .env pour activer les logs SQL.
    app_env = os.environ.get("APP_ENV", "dev")
    sql_echo = (app_env == "dev_debug")

    # Creation de l'moteur de base de donnees (PostgreSQL)
    _engine = create_engine(
        db_url,
        echo=sql_echo,
        pool_pre_ping=True # Verifie la connexion avant d'envoyer des requetes
    )
    
    # Configurateur de session locale
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine

def test_connection() -> bool:
    """Verifie reellement la connexion a la base de donnees."""
    global _engine
    if _engine is None:
        init_db()
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        raise Exception(f"Erreur de connexion PostgreSQL: {str(e)}")

def get_session():
    """Genere une session autonome temporaire pour executer des requetes."""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()

def create_tables():
    """Cree toutes les tables SQLAlchemy dans la base PostgreSQL si elles n'existent pas."""
    global _engine
    if _engine is None:
        init_db()
    # Importation de tous les modeles pour s'assurer que SQLAlchemy les connaisse avant la creation
    import models.etablissement
    import models.annee_scolaire
    import models.cycle
    import models.niveau
    import models.classe
    import models.nationalite
    import models.religion
    import models.famille
    import models.eleve
    import models.inscription
    import models.autres_frais
    import models.montant_autres_frais
    import models.montant_scol
    import models.montant_cantine
    import models.montant_transport
    import models.versement_scol
    import models.article
    import models.stock_cour
    import models.stock_entree
    import models.stock_sortie
    import models.compte
    import models.type_sortie
    import models.sortie_fin
    import models.profil
    import models.permission
    import models.profil_permission
    import models.utilisateur
    import models.prestataire
    import models.prestation_annexe
    import models.ventilation_prestation

    Base.metadata.create_all(bind=_engine)
    print("Tables creees avec succes dans PostgreSQL !")
    
    # Idempotent upgrade of VersementScol to add MontantCantine and MontantVersAutres fields if they already existed
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "VersementScol" ADD COLUMN IF NOT EXISTS "MontantCantine" NUMERIC(12,2) DEFAULT 0;'))
            conn.execute(text('ALTER TABLE IF EXISTS "VersementScol" ADD COLUMN IF NOT EXISTS "MontantVersAutres" NUMERIC(12,2) DEFAULT 0;'))
            print("Mise a jour de table 'VersementScol' (ajout colonnes) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration 'VersementScol': {e}")

    # Idempotent upgrade: imprimante par défaut par utilisateur
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "Utilisateur" ADD COLUMN IF NOT EXISTS "ImprimanteDefaut" VARCHAR(255);'))
            print("Mise a jour de table 'Utilisateur' (ajout colonne ImprimanteDefaut) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration 'Utilisateur': {e}")

    # Ventilation analytique : index de performance sur (IDEleve, IDAnneeScolaire)
    try:
        with _engine.begin() as conn:
            conn.execute(text(
                'CREATE INDEX IF NOT EXISTS idx_ventilation_eleve_annee '
                'ON "VentilationPrestation" ("IDEleve", "IDAnneeScolaire");'
            ))
            print("Index VentilationPrestation créé (ou déjà présent).")
    except Exception as e:
        print(f"Avertissement index VentilationPrestation : {e}")
