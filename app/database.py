import os
import re
import unicodedata
from collections import Counter
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
    import models.montant_scol
    import models.montant_cantine
    import models.montant_transport
    import models.versement_scol
    import models.echeance_paiement
    import models.article
    import models.stock_cour
    import models.stock_entree
    import models.stock_sortie
    import models.kit_composant
    import models.kit_assemblage
    import models.compte
    import models.type_sortie
    import models.sortie_fin
    import models.profil
    import models.permission
    import models.profil_permission
    import models.utilisateur
    import models.prestataire
    import models.prestation_annexe
    import models.prestation_tarif_niveau
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
            conn.execute(text('ALTER TABLE IF EXISTS "Utilisateur" ADD COLUMN IF NOT EXISTS "MustChangePassword" BOOLEAN DEFAULT FALSE NOT NULL;'))
            print("Mise a jour de table 'Utilisateur' (colonnes preferences/securite) terminee avec succes.")
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

    # Fusion "Autres Frais" (Autres_Frais / MontantAutresFrais) dans le moteur de
    # ventilation PrestationAnnexe : chaque type de frais annexe devient une
    # PrestationAnnexe (ou est rattache a une prestation existante de meme libelle),
    # et ses tarifs par niveau sont repris dans PrestationTarifNiveau. Les anciennes
    # tables ne sont pas supprimees (historique conserve, plus utilisees par l'appli).
    try:
        with _engine.begin() as conn:
            table_existe = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'Autres_Frais')"
            )).scalar()

            if table_existe:
                deja_migre = conn.execute(text('SELECT COUNT(*) FROM "PrestationTarifNiveau"')).scalar()
                if not deja_migre:
                    def _normaliser(libelle: str) -> str:
                        texte = unicodedata.normalize("NFKD", libelle or "")
                        texte = "".join(c for c in texte if not unicodedata.combining(c))
                        return re.sub(r"[^A-Z0-9]", "", texte.upper())

                    prestations = conn.execute(text(
                        'SELECT "IDPrestation", "Libelle" FROM "PrestationAnnexe"'
                    )).fetchall()
                    prestation_par_libelle = {_normaliser(p.Libelle): p.IDPrestation for p in prestations}

                    types_frais = conn.execute(text(
                        'SELECT "IDAutres_Frais", "CodeFrais", "LibelleFrais" FROM "Autres_Frais"'
                    )).fetchall()

                    mapping = {}
                    for t in types_frais:
                        cle = _normaliser(t.LibelleFrais)
                        id_prestation = prestation_par_libelle.get(cle)
                        if id_prestation is None:
                            montants = conn.execute(text(
                                'SELECT "MontantFrais" FROM "MontantAutresFrais" WHERE "IDAutres_Frais" = :id'
                            ), {"id": t.IDAutres_Frais}).scalars().all()
                            montant_defaut = Counter(montants).most_common(1)[0][0] if montants else 0
                            id_prestation = conn.execute(text(
                                'INSERT INTO "PrestationAnnexe" ("Code", "Libelle", "MontantAnnuel", "IsActive") '
                                'VALUES (:code, :libelle, :montant, TRUE) RETURNING "IDPrestation"'
                            ), {"code": t.CodeFrais, "libelle": t.LibelleFrais, "montant": montant_defaut}).scalar()
                            prestation_par_libelle[cle] = id_prestation
                        mapping[t.IDAutres_Frais] = id_prestation

                    for id_autres_frais, id_prestation in mapping.items():
                        conn.execute(text('''
                            INSERT INTO "PrestationTarifNiveau" ("IDAnneeScolaire", "IDT_Niveau", "IDPrestation", "MontantAnnuel")
                            SELECT "IDAnneeScolaire", "IDT_Niveau", :id_prestation, "MontantFrais"
                            FROM "MontantAutresFrais"
                            WHERE "IDAutres_Frais" = :id_autres_frais
                            ON CONFLICT ("IDAnneeScolaire", "IDT_Niveau", "IDPrestation") DO NOTHING;
                        '''), {"id_prestation": id_prestation, "id_autres_frais": id_autres_frais})

                    print(f"Migration Autres Frais -> Prestations annexes : {len(mapping)} type(s) traite(s).")
    except Exception as e:
        print(f"Avertissement migration Autres Frais -> Prestations annexes : {e}")

    # Idempotent upgrade: proteger l'historique sensible contre les suppressions
    # indirectes. Les anciennes bases pouvaient avoir ON DELETE CASCADE sur les
    # inscriptions et versements ; on remplace ces FK par ON DELETE RESTRICT.
    critical_restrict_fks = [
        ("TInscription", "TInscription_IDTAnneeScolaire_fkey", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
        ("TInscription", "TInscription_IDFamille_fkey", "IDFamille", "TFamille", "IdTFamille"),
        ("TInscription", "TInscription_IDEleve_fkey", "IDEleve", "Eleve", "IDEleve"),
        ("TInscription", "TInscription_IDNiveau_fkey", "IDNiveau", "TNiveau", "IDT_Niveau"),
        ("TInscription", "TInscription_IDClasse_fkey", "IDClasse", "TClasse", "IDTClasse"),
        ("VersementScol", "VersementScol_IDFamille_fkey", "IDFamille", "TFamille", "IdTFamille"),
        ("VersementScol", "VersementScol_IDTAnneeScolaire_fkey", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
        ("VersementScol", "VersementScol_IDEleve_fkey", "IDEleve", "Eleve", "IDEleve"),
        ("StockCour", "StockCour_IDTArticle_fkey", "IDTArticle", "TArticle", "IDTArticle"),
        ("StockEnt", "StockEnt_IDTAnneeScolaire_fkey", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
        ("StockEnt", "StockEnt_IDTArticle_fkey", "IDTArticle", "TArticle", "IDTArticle"),
        ("StockSortie", "StockSortie_IDTAnneeScolaire_fkey", "IDTAnneeScolaire", "TAnneeScolaire", "IDTAnneeScolaire"),
        ("StockSortie", "StockSortie_IDTArticle_fkey", "IDTArticle", "TArticle", "IDTArticle"),
    ]
    try:
        with _engine.begin() as conn:
            for table_name, constraint_name, column_name, ref_table, ref_column in critical_restrict_fks:
                conn.execute(text(f'''
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.referential_constraints rc
        JOIN information_schema.table_constraints tc
          ON tc.constraint_schema = rc.constraint_schema
         AND tc.constraint_name = rc.constraint_name
        WHERE tc.table_schema = 'public'
          AND tc.table_name = '{table_name}'
          AND tc.constraint_name = '{constraint_name}'
          AND rc.delete_rule <> 'RESTRICT'
    ) THEN
        ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}";
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = '{table_name}'
          AND constraint_name = '{constraint_name}'
    ) THEN
        ALTER TABLE "{table_name}"
        ADD CONSTRAINT "{constraint_name}"
        FOREIGN KEY ("{column_name}") REFERENCES "{ref_table}" ("{ref_column}")
        ON DELETE RESTRICT;
    END IF;
END $$;
'''))
            print("Contraintes critiques d'historique verifiees en ON DELETE RESTRICT.")
    except Exception as e:
        print(f"Avertissement migration contraintes historiques : {e}")

    # Integrite kiosque pour les bases deja existantes.
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "ReferenceVente" VARCHAR(36);'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "PrixCatalogue" NUMERIC(12,2);'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "RemiseMontant" NUMERIC(12,2) NOT NULL DEFAULT 0;'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "MotifRemise" VARCHAR(255);'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "Statut" VARCHAR(20) NOT NULL DEFAULT \'VALIDE\';'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "DateAnnulation" TIMESTAMP;'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "LoginAnnulation" VARCHAR(50);'))
            conn.execute(text('ALTER TABLE IF EXISTS "StockSortie" ADD COLUMN IF NOT EXISTS "MotifAnnulation" VARCHAR(255);'))
            conn.execute(text('UPDATE "StockSortie" SET "ReferenceVente" = gen_random_uuid()::text WHERE "ReferenceVente" IS NULL;'))
            conn.execute(text('UPDATE "StockSortie" SET "PrixCatalogue" = "Prix_vente" WHERE "PrixCatalogue" IS NULL;'))
            checks = [
                ("TArticle", "ck_article_pu_non_negatif", '"PU" >= 0'),
                ("TArticle", "ck_article_seuil_non_negatif", '"QTESeuil" >= 0'),
                ("StockCour", "ck_stock_cour_non_negatif", '"QuantiteCour" >= 0'),
                ("StockEnt", "ck_stock_entree_positive", '"QuantiteEnt" > 0'),
                ("StockSortie", "ck_stock_sortie_positive", '"QuantiteSort" > 0'),
                ("StockSortie", "ck_stock_sortie_prix_non_negatif", '"Prix_vente" >= 0'),
            ]
            for table_name, constraint_name, expression in checks:
                conn.execute(text(f'''
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{constraint_name}') THEN
        ALTER TABLE "{table_name}" ADD CONSTRAINT "{constraint_name}" CHECK ({expression});
    END IF;
END $$;
'''))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_stock_sortie_reference ON "StockSortie" ("ReferenceVente");'))
            conn.execute(text('''
INSERT INTO "KitComposant" ("IDKit", "IDArticle", "Quantite")
SELECT kit."IDTArticle", ids.val::integer, qtes.val::integer
FROM "TArticle" kit
JOIN LATERAL unnest(string_to_array(kit."ContenuKit", ';')) WITH ORDINALITY ids(val, ord) ON true
JOIN LATERAL unnest(string_to_array(kit."QteKit", ';')) WITH ORDINALITY qtes(val, ord) ON qtes.ord = ids.ord
JOIN "TArticle" composant ON composant."IDTArticle" = ids.val::integer AND composant."KIT" = false
WHERE kit."KIT" = true AND ids.val ~ '^\\d+$' AND qtes.val ~ '^[1-9]\\d*$'
ON CONFLICT ("IDKit", "IDArticle") DO NOTHING;
'''))
    except Exception as e:
        print(f"Avertissement migration integrite kiosque : {e}")

    # Idempotent upgrade: ContactUrgence pouvait contenir plusieurs numeros
    # separes par "/" et depassait la limite historique de varchar(20).
    try:
        with _engine.begin() as conn:
            conn.execute(text('ALTER TABLE IF EXISTS "TFamille" ALTER COLUMN "ContactUrgence" TYPE VARCHAR(50);'))
            print("Colonne 'TFamille.ContactUrgence' elargie a VARCHAR(50).")
    except Exception as e:
        print(f"Avertissement migration 'TFamille.ContactUrgence': {e}")

    # Coordonnees officielles de l'etablissement pour les bases existantes.
    try:
        with _engine.begin() as conn:
            conn.execute(text(
                'ALTER TABLE IF EXISTS "Etablissement_Ecole" '
                'ADD COLUMN IF NOT EXISTS "TelephoneSecondaire" VARCHAR(50);'
            ))
            conn.execute(text(
                'ALTER TABLE IF EXISTS "Etablissement_Ecole" '
                'ADD COLUMN IF NOT EXISTS "AdressePostale" VARCHAR(100);'
            ))
            conn.execute(text(
                'ALTER TABLE IF EXISTS "Etablissement_Ecole" '
                'ALTER COLUMN "Adresse" TYPE VARCHAR(170);'
            ))
    except Exception as e:
        print(f"Avertissement migration coordonnees etablissement : {e}")
