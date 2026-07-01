from app.database import get_session
from models.profil import Profil
from models.profil_permission import ProfilPermission
from models.permission import Permission

# Profils par défaut avec leurs permissions initiales
_DEFAULT_PROFILES = [
    {
        "Code": "ADMIN",
        "Libelle": "Administrateur",
        "Description": "Accès complet à toutes les fonctionnalités",
        "IsAdmin": True,
        "permissions": "ALL",
    },
    {
        "Code": "DIRECTEUR",
        "Libelle": "Directeur",
        "Description": "Accès à la gestion scolaire et aux statistiques",
        "IsAdmin": False,
        "permissions": [
            "DASHBOARD_VIEW", "SCOLARITE_VIEW", "SCOLARITE_ELEVES",
            "SCOLARITE_INSCRIPTIONS", "SCOLARITE_VERSEMENTS",
            "KIOSQUE_VIEW", "STATISTIQUES_VIEW", "PARAMETRES_VIEW",
        ],
    },
    {
        "Code": "COMPTABLE",
        "Libelle": "Comptable",
        "Description": "Accès à la comptabilité et aux versements",
        "IsAdmin": False,
        "permissions": [
            "DASHBOARD_VIEW", "SCOLARITE_VIEW", "SCOLARITE_VERSEMENTS",
            "COMPTABILITE_VIEW", "COMPTABILITE_SAISIE", "STATISTIQUES_VIEW",
        ],
    },
    {
        "Code": "SECRETAIRE",
        "Libelle": "Secrétaire",
        "Description": "Gestion des inscriptions et des élèves",
        "IsAdmin": False,
        "permissions": [
            "DASHBOARD_VIEW", "SCOLARITE_VIEW", "SCOLARITE_ELEVES",
            "SCOLARITE_INSCRIPTIONS", "KIOSQUE_VIEW", "KIOSQUE_VENTES",
        ],
    },
]


class ProfilService:

    @staticmethod
    def seed_default_profiles():
        """Crée les profils par défaut s'ils n'existent pas encore (idempotent)."""
        session = get_session()
        try:
            all_perms = session.query(Permission).all()
            perm_by_code = {p.Code: p for p in all_perms}

            for pdata in _DEFAULT_PROFILES:
                existing = session.query(Profil).filter_by(Code=pdata["Code"]).first()
                if not existing:
                    profil = Profil(
                        Code=pdata["Code"],
                        Libelle=pdata["Libelle"],
                        Description=pdata["Description"],
                        IsAdmin=pdata["IsAdmin"],
                    )
                    session.add(profil)
                    session.flush()

                    codes = list(perm_by_code.keys()) if pdata["permissions"] == "ALL" else pdata["permissions"]
                    for code in codes:
                        if code in perm_by_code:
                            session.add(ProfilPermission(
                                IDProfil=profil.IDProfil,
                                IDPermission=perm_by_code[code].IDPermission,
                                Accordee=True,
                            ))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur seeding profils : {e}")
        finally:
            session.close()

    @staticmethod
    def get_all() -> list[Profil]:
        session = get_session()
        try:
            return session.query(Profil).order_by(Profil.Libelle.asc()).all()
        finally:
            session.close()

    @staticmethod
    def get_by_id(id_profil: int) -> Profil | None:
        session = get_session()
        try:
            return session.get(Profil, id_profil)
        finally:
            session.close()

    @staticmethod
    def count_users(id_profil: int) -> int:
        from models.utilisateur import Utilisateur
        session = get_session()
        try:
            return session.query(Utilisateur).filter_by(IDProfil=id_profil).count()
        finally:
            session.close()

    @staticmethod
    def create(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            code = data.get("Code", "").strip().upper()
            libelle = data.get("Libelle", "").strip()
            if not code:
                return False, "Le code est obligatoire."
            if not libelle:
                return False, "Le libellé est obligatoire."
            if session.query(Profil).filter_by(Code=code).first():
                return False, f"Un profil avec le code '{code}' existe déjà."
            profil = Profil(
                Code=code,
                Libelle=libelle,
                Description=data.get("Description", "").strip() or None,
                IsAdmin=data.get("IsAdmin", False),
            )
            session.add(profil)
            session.commit()
            return True, f"Profil '{libelle}' créé avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update(id_profil: int, data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            profil = session.get(Profil, id_profil)
            if not profil:
                return False, "Profil introuvable."
            code = data.get("Code", "").strip().upper()
            libelle = data.get("Libelle", "").strip()
            if not code:
                return False, "Le code est obligatoire."
            if not libelle:
                return False, "Le libellé est obligatoire."
            doublon = session.query(Profil).filter(
                (Profil.Code == code) & (Profil.IDProfil != id_profil)
            ).first()
            if doublon:
                return False, f"Le code '{code}' est déjà utilisé par un autre profil."
            profil.Code = code
            profil.Libelle = libelle
            profil.Description = data.get("Description", "").strip() or None
            profil.IsAdmin = data.get("IsAdmin", profil.IsAdmin)
            session.commit()
            return True, "Profil mis à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete(id_profil: int) -> tuple[bool, str]:
        from models.utilisateur import Utilisateur
        session = get_session()
        try:
            profil = session.get(Profil, id_profil)
            if not profil:
                return False, "Profil introuvable."
            if session.query(Utilisateur).filter_by(IDProfil=id_profil).first():
                return False, "Impossible de supprimer ce profil : des utilisateurs y sont rattachés."
            session.query(ProfilPermission).filter_by(IDProfil=id_profil).delete()
            session.delete(profil)
            session.commit()
            return True, f"Profil '{profil.Libelle}' supprimé avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_profil_permissions(id_profil: int) -> set[str]:
        """Retourne les codes de permission accordés à un profil."""
        session = get_session()
        try:
            rows = (
                session.query(ProfilPermission, Permission)
                .join(Permission, ProfilPermission.IDPermission == Permission.IDPermission)
                .filter(
                    ProfilPermission.IDProfil == id_profil,
                    ProfilPermission.Accordee == True,
                )
                .all()
            )
            return {row.Permission.Code for row in rows}
        finally:
            session.close()

    @staticmethod
    def set_profil_permissions(id_profil: int, codes_accordes: set[str]) -> tuple[bool, str]:
        """Remplace toutes les permissions d'un profil par les codes fournis."""
        session = get_session()
        try:
            all_perms = session.query(Permission).all()
            session.query(ProfilPermission).filter_by(IDProfil=id_profil).delete()
            for perm in all_perms:
                session.add(ProfilPermission(
                    IDProfil=id_profil,
                    IDPermission=perm.IDPermission,
                    Accordee=(perm.Code in codes_accordes),
                ))
            session.commit()
            return True, "Droits mis à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()
