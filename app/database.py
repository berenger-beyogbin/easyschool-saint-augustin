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
    import models.inscription_autres_frais
    import models.montant_scol
    import models.montant_cantine
    import models.montant_transport
    import models.versement_scol
    import models.versement_autres_frais
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
    import models.audit_log

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

    # Idempotent upgrade : statut d'affectation de l'État sur les inscriptions
    try:
        with _engine.begin() as conn:
            conn.execute(text(
                'ALTER TABLE IF EXISTS "TInscription" '
                'ADD COLUMN IF NOT EXISTS "StatutAffectation" VARCHAR(20) NOT NULL DEFAULT \'AFFECTE_ETAT\';'
            ))
            print("Mise a jour de table 'TInscription' (ajout colonne StatutAffectation) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration 'TInscription': {e}")

    # Suppression du tarif de scolarité "catégorie enseignant" : la scolarité
    # ne repose plus que sur le montant standard.
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "MontantScol" DROP COLUMN IF EXISTS "MontantEnsPri";'))
            conn.execute(text('ALTER TABLE IF EXISTS "MontantScol" DROP COLUMN IF EXISTS "MontantEnsSecondaire";'))
            conn.execute(text('ALTER TABLE IF EXISTS "TFamille" DROP COLUMN IF EXISTS "EnsCatPrimaire";'))
            conn.execute(text('ALTER TABLE IF EXISTS "TFamille" DROP COLUMN IF EXISTS "EnsCatSecondaire";'))
            print("Suppression des colonnes de tarif enseignant (MontantScol/TFamille) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration tarif enseignant : {e}")

    # Colonne "MustChangePassword" : residu d'un ancien schema, jamais utilisee
    # par le modele Utilisateur actuel. Sa presence (NOT NULL sans defaut) fait
    # echouer toute creation d'utilisateur sur une base deja initialisee avant
    # sa suppression du modele.
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "Utilisateur" DROP COLUMN IF EXISTS "MustChangePassword";'))
            print("Suppression de la colonne obsolete 'MustChangePassword' (Utilisateur) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration 'Utilisateur' (MustChangePassword) : {e}")

    # Scolarité à deux tarifs selon le statut d'affectation de l'État
    # (Non affecté / Affecté, cf. TInscription.StatutAffectation) : remplace
    # l'ancien montant unique "Montant" par MontantNonAffecte / MontantAffecte,
    # en reprenant l'ancienne valeur comme point de depart pour les deux.
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "MontantScol" ADD COLUMN IF NOT EXISTS "MontantNonAffecte" NUMERIC(12,2) NOT NULL DEFAULT 0;'))
            conn.execute(text('ALTER TABLE IF EXISTS "MontantScol" ADD COLUMN IF NOT EXISTS "MontantAffecte" NUMERIC(12,2) NOT NULL DEFAULT 0;'))
            has_montant = conn.execute(text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'MontantScol' AND column_name = 'Montant';"
            )).first()
            if has_montant:
                conn.execute(text('UPDATE "MontantScol" SET "MontantNonAffecte" = "Montant", "MontantAffecte" = "Montant";'))
                conn.execute(text('ALTER TABLE "MontantScol" DROP COLUMN "Montant";'))
            print("Mise a jour de table 'MontantScol' (tarifs Non affecte/Affecte) terminee avec succes.")
    except Exception as e:
        print(f"Avertissement migration 'MontantScol' (tarifs affectation) : {e}")

    # Contraintes d'integrite financiere : ajoutees ici pour les bases deja
    # initialisees avant leur introduction dans les modeles (create_all ne les
    # ajoute que sur les tables neuves). Ajout idempotent via verification de
    # pg_constraint pour ne pas echouer si deja presentes.
    integrity_constraints = [
        ('uq_versement_autres_frais_inscription',
         'ALTER TABLE "VersementAutresFrais" ADD CONSTRAINT uq_versement_autres_frais_inscription '
         'UNIQUE ("IDInscriptionAutresFrais")'),
        ('ck_versement_scol_trans_positif',
         'ALTER TABLE "VersementScol" ADD CONSTRAINT ck_versement_scol_trans_positif '
         'CHECK ("MontantVersTrans" >= 0)'),
        ('ck_versement_scol_sco_positif',
         'ALTER TABLE "VersementScol" ADD CONSTRAINT ck_versement_scol_sco_positif '
         'CHECK ("MontantVersSco" >= 0)'),
        ('ck_versement_scol_cantine_positif',
         'ALTER TABLE "VersementScol" ADD CONSTRAINT ck_versement_scol_cantine_positif '
         'CHECK ("MontantCantine" >= 0)'),
        ('ck_versement_scol_autres_positif',
         'ALTER TABLE "VersementScol" ADD CONSTRAINT ck_versement_scol_autres_positif '
         'CHECK ("MontantVersAutres" >= 0)'),
        ('ck_inscription_autres_frais_montant_positif',
         'ALTER TABLE "InscriptionAutresFrais" ADD CONSTRAINT ck_inscription_autres_frais_montant_positif '
         'CHECK ("MontantApplique" >= 0)'),
        ('ck_montant_scol_non_affecte_positif',
         'ALTER TABLE "MontantScol" ADD CONSTRAINT ck_montant_scol_non_affecte_positif '
         'CHECK ("MontantNonAffecte" >= 0)'),
        ('ck_montant_scol_affecte_positif',
         'ALTER TABLE "MontantScol" ADD CONSTRAINT ck_montant_scol_affecte_positif '
         'CHECK ("MontantAffecte" >= 0)'),
    ]
    try:
        with _engine.begin() as conn:
            for constraint_name, ddl in integrity_constraints:
                exists = conn.execute(
                    text("SELECT 1 FROM pg_constraint WHERE conname = :name"),
                    {"name": constraint_name},
                ).first()
                if not exists:
                    conn.execute(text(ddl))
            print("Contraintes d'integrite financiere verifiees/ajoutees avec succes.")
    except Exception as e:
        print(f"Avertissement migration contraintes d'integrite : {e}")
