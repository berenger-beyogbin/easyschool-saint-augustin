from app.database import get_session
from models.permission import Permission
import logging
logger = logging.getLogger(__name__)


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
    ("STAT_INSCRITS_VIEW",      "Statistique — Élèves inscrits",         "Statistiques",     51),
    ("STAT_NOUVEAUX_VIEW",      "Statistique — Nouveaux élèves",         "Statistiques",     52),
    ("STAT_SCOLARITE_VIEW",     "Statistique — Versements scolarité",    "Statistiques",     53),
    ("STAT_INTERNAT_VIEW",      "Statistique — Internat",                "Statistiques",     54),
    ("STAT_CANTINE_VIEW",       "Statistique — Cantine",                 "Statistiques",     55),
    ("STAT_TRANSPORT_VIEW",     "Statistique — Transport",               "Statistiques",     56),
    ("STAT_VENTE_VIEW",         "Statistique — Ventes (Kiosque)",        "Statistiques",     57),
    ("STAT_STOCK_VIEW",         "Statistique — Stock",                   "Statistiques",     58),
    ("STAT_ALPHABETIQUE_VIEW",  "Statistique — Liste alphabétique",      "Statistiques",     59),
    ("STAT_PERIODIQUE_VIEW",    "Statistique — État périodique",         "Statistiques",     60),
    ("SMS_VIEW",                "Accès au module SMS",                   "SMS",              60),
    ("PARAMETRES_VIEW",         "Accès aux paramètres",                  "Paramètres",       70),
    ("PARAMETRES_MODIFIER",     "Modification des paramètres",           "Paramètres",       71),
    ("UTILISATEURS_VIEW",       "Accès à la gestion des utilisateurs",   "Utilisateurs",     80),
    ("UTILISATEURS_MODIFIER",   "Modification des utilisateurs/profils", "Utilisateurs",     81),
    ("INTERNAT_VIEW",           "Accès au module Internat",              "Internat",         90),
    ("INTERNAT_ADMISSIONS",     "Gestion des admissions et dossiers",    "Internat",         91),
    ("INTERNAT_VERSEMENTS",     "Encaissement des pensions",             "Internat",         92),
    ("INTERNAT_PARAMETRES",     "Paramétrage des tarifs de l'internat",  "Internat",         93),
    ("CANTINE_EXTERNE_VIEW",        "Accès au module Cantine externe",       "Cantine externe",  100),
    ("CANTINE_EXTERNE_ADMISSIONS",  "Gestion des inscriptions cantine",      "Cantine externe",  101),
    ("CANTINE_EXTERNE_VERSEMENTS",  "Encaissement de la cantine externe",    "Cantine externe",  102),
    ("CANTINE_EXTERNE_PARAMETRES",  "Paramétrage du tarif de la cantine",    "Cantine externe",  103),
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
        except Exception:
            session.rollback()
            logger.exception("Erreur seeding permissions")
        finally:
            session.close()

    @staticmethod
    def backfill_stat_sub_permissions():
        """Migration ponctuelle : STATISTIQUES_VIEW a ete decoupe en
        permissions plus fines (un rapport par onglet). Les profils qui
        avaient deja STATISTIQUES_VIEW doivent conserver l'acces a TOUS
        les rapports (comportement identique a avant ce decoupage), sinon
        ils perdraient silencieusement l'affichage de tous les onglets
        Statistiques au prochain demarrage. Idempotent : n'ajoute que les
        lignes ProfilPermission manquantes, ne modifie jamais un choix
        deja fait explicitement par un administrateur."""
        from models.profil_permission import ProfilPermission

        session = get_session()
        try:
            stat_view = session.query(Permission).filter_by(Code="STATISTIQUES_VIEW").first()
            if not stat_view:
                return

            sub_codes = [
                code for code, _, module, _ in PERMISSIONS_CATALOG
                if module == "Statistiques" and code != "STATISTIQUES_VIEW"
            ]
            sub_perms = session.query(Permission).filter(Permission.Code.in_(sub_codes)).all()
            if not sub_perms:
                return

            id_profils_avec_stats = {
                row[0] for row in session.query(ProfilPermission.IDProfil).filter(
                    ProfilPermission.IDPermission == stat_view.IDPermission,
                    ProfilPermission.Accordee == True,
                ).all()
            }
            if not id_profils_avec_stats:
                return

            existing = {
                (row[0], row[1]) for row in session.query(
                    ProfilPermission.IDProfil, ProfilPermission.IDPermission
                ).filter(
                    ProfilPermission.IDProfil.in_(id_profils_avec_stats),
                    ProfilPermission.IDPermission.in_([p.IDPermission for p in sub_perms]),
                ).all()
            }

            for id_profil in id_profils_avec_stats:
                for perm in sub_perms:
                    if (id_profil, perm.IDPermission) not in existing:
                        session.add(ProfilPermission(
                            IDProfil=id_profil, IDPermission=perm.IDPermission, Accordee=True
                        ))
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Erreur backfill_stat_sub_permissions")
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
