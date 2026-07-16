from app.database import get_session
from models.permission import Permission

# Catalogue complet des fonctionnalités de l'application
PERMISSIONS_CATALOG = [
    # (Code, Libelle, Module, Ordre)
    ("DASHBOARD_VIEW",          "Accès au tableau de bord",              "Tableau de bord",  10),
    ("SCOLARITE_VIEW",          "Accès au module Scolarité",             "Scolarité",        20),
    ("SCOLARITE_ELEVES",        "Gestion des élèves",                    "Scolarité",        21),
    ("SCOLARITE_INSCRIPTIONS",  "Gestion des inscriptions",              "Scolarité",        22),
    ("SCOLARITE_VERSEMENTS",    "Gestion des versements",                "Scolarité",        23),
    ("KIOSQUE_VIEW",            "Accès au module Kiosque",               "Kiosque",          30),
    ("KIOSQUE_VENTES",          "Gestion des ventes",                    "Kiosque",          31),
    ("KIOSQUE_ARTICLES",        "Gestion des articles",                  "Kiosque",          32),
    ("KIOSQUE_STOCKS",          "Gestion des stocks",                    "Kiosque",          33),
    ("COMPTABILITE_VIEW",       "Accès au module Comptabilité",          "Comptabilité",     40),
    ("COMPTABILITE_SAISIE",     "Saisie des opérations comptables",      "Comptabilité",     41),
    ("STATISTIQUES_VIEW",       "Accès aux statistiques",                "Statistiques",     50),
    ("SMS_VIEW",                "Accès au module SMS",                   "SMS",              60),
    ("PARAMETRES_VIEW",         "Accès aux paramètres",                  "Paramètres",       70),
    ("PARAMETRES_MODIFIER",     "Modification des paramètres",           "Paramètres",       71),
    ("UTILISATEURS_VIEW",       "Accès à la gestion des utilisateurs",   "Utilisateurs",     80),
    ("UTILISATEURS_MODIFIER",   "Modification des utilisateurs/profils", "Utilisateurs",     81),
]


class PermissionService:

    @staticmethod
    def seed_permissions():
        """Insère les permissions manquantes du catalogue (idempotent)."""
        session = get_session()
        try:
            for code, libelle, module, ordre in PERMISSIONS_CATALOG:
                if not session.query(Permission).filter_by(Code=code).first():
                    session.add(Permission(Code=code, Libelle=libelle, Module=module, Ordre=ordre))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur seeding permissions : {e}")
        finally:
            session.close()

    @staticmethod
    def get_all() -> list[Permission]:
        session = get_session()
        try:
            return session.query(Permission).order_by(Permission.Ordre.asc()).all()
        finally:
            session.close()

    @staticmethod
    def get_by_module() -> dict[str, list[Permission]]:
        """Retourne les permissions regroupées par module (ordre conservé)."""
        by_module: dict[str, list[Permission]] = {}
        for p in PermissionService.get_all():
            by_module.setdefault(p.Module, []).append(p)
        return by_module
