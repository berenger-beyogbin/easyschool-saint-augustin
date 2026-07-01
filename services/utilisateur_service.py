import hashlib
import os
from datetime import datetime
from app.database import get_session
from models.utilisateur import Utilisateur
from models.profil import Profil
from sqlalchemy.orm import joinedload


# ---------------------------------------------------------------------------
# Hachage des mots de passe (PBKDF2-SHA256, stdlib uniquement)
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"{salt}:{h.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
        return computed.hex() == h
    except Exception:
        return False


class UtilisateurService:

    @staticmethod
    def seed_default_admin():
        """Crée le compte administrateur par défaut si aucun utilisateur n'existe."""
        session = get_session()
        try:
            if session.query(Utilisateur).count() > 0:
                return
            admin_profil = session.query(Profil).filter_by(Code="ADMIN").first()
            if not admin_profil:
                return
            admin = Utilisateur(
                Login="admin",
                MotDePasseHash=_hash_password("admin123"),
                Nom="Administrateur",
                Prenoms="Système",
                IDProfil=admin_profil.IDProfil,
                IsActive=True,
            )
            session.add(admin)
            session.commit()
            print("Compte admin créé — login: admin / mot de passe: admin123")
        except Exception as e:
            session.rollback()
            print(f"Erreur seeding admin : {e}")
        finally:
            session.close()

    @staticmethod
    def authenticate(login: str, password: str) -> tuple[bool, str, dict | None]:
        """
        Authentifie un utilisateur.
        Retourne (succès, message, user_data_dict) où user_data_dict contient
        les informations de session sans dépendance à la session SQLAlchemy.
        """
        session = get_session()
        try:
            user = (
                session.query(Utilisateur)
                .options(joinedload(Utilisateur.profil))
                .filter_by(Login=login.strip())
                .first()
            )
            if not user:
                return False, "Identifiant inconnu.", None
            if not user.IsActive:
                return False, "Ce compte est désactivé. Contactez l'administrateur.", None
            if not _verify_password(password, user.MotDePasseHash):
                return False, "Mot de passe incorrect.", None

            user.DernierAcces = datetime.now()
            session.commit()

            user_data = {
                "IDUtilisateur": user.IDUtilisateur,
                "Login": user.Login,
                "Nom": user.Nom,
                "Prenoms": user.Prenoms or "",
                "Email": user.Email or "",
                "IDProfil": user.IDProfil,
                "ProfilCode": user.profil.Code if user.profil else "",
                "ProfilLibelle": user.profil.Libelle if user.profil else "",
                "IsAdmin": user.profil.IsAdmin if user.profil else False,
                "ImprimanteDefaut": user.ImprimanteDefaut or None,
            }
            return True, "Connexion réussie.", user_data
        except Exception as e:
            return False, f"Erreur d'authentification : {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def get_all() -> list[Utilisateur]:
        session = get_session()
        try:
            return (
                session.query(Utilisateur)
                .options(joinedload(Utilisateur.profil))
                .order_by(Utilisateur.Nom.asc())
                .all()
            )
        finally:
            session.close()

    @staticmethod
    def get_by_id(id_user: int) -> Utilisateur | None:
        session = get_session()
        try:
            return (
                session.query(Utilisateur)
                .options(joinedload(Utilisateur.profil))
                .filter_by(IDUtilisateur=id_user)
                .first()
            )
        finally:
            session.close()

    @staticmethod
    def create(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            login = data.get("Login", "").strip()
            nom = data.get("Nom", "").strip()
            password = data.get("Password", "").strip()
            id_profil = data.get("IDProfil")

            if not login:
                return False, "Le login est obligatoire."
            if not nom:
                return False, "Le nom est obligatoire."
            if not password:
                return False, "Le mot de passe est obligatoire."
            if len(password) < 6:
                return False, "Le mot de passe doit contenir au moins 6 caractères."
            if not id_profil:
                return False, "Le profil est obligatoire."

            if session.query(Utilisateur).filter_by(Login=login).first():
                return False, f"Le login '{login}' est déjà utilisé."

            user = Utilisateur(
                Login=login,
                MotDePasseHash=_hash_password(password),
                Nom=nom,
                Prenoms=data.get("Prenoms", "").strip() or None,
                Email=data.get("Email", "").strip() or None,
                IDProfil=id_profil,
                IsActive=data.get("IsActive", True),
            )
            session.add(user)
            session.commit()
            return True, f"Utilisateur '{login}' créé avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update(id_user: int, data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            user = session.query(Utilisateur).get(id_user)
            if not user:
                return False, "Utilisateur introuvable."

            login = data.get("Login", "").strip()
            nom = data.get("Nom", "").strip()
            if not login:
                return False, "Le login est obligatoire."
            if not nom:
                return False, "Le nom est obligatoire."

            doublon = session.query(Utilisateur).filter(
                (Utilisateur.Login == login) & (Utilisateur.IDUtilisateur != id_user)
            ).first()
            if doublon:
                return False, f"Le login '{login}' est déjà utilisé par un autre compte."

            user.Login = login
            user.Nom = nom
            user.Prenoms = data.get("Prenoms", "").strip() or None
            user.Email = data.get("Email", "").strip() or None
            user.IDProfil = data.get("IDProfil", user.IDProfil)
            user.IsActive = data.get("IsActive", user.IsActive)

            new_pwd = data.get("Password", "").strip()
            if new_pwd:
                if len(new_pwd) < 6:
                    return False, "Le mot de passe doit contenir au moins 6 caractères."
                user.MotDePasseHash = _hash_password(new_pwd)

            session.commit()
            return True, "Utilisateur mis à jour avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def toggle_active(id_user: int) -> tuple[bool, str]:
        session = get_session()
        try:
            user = session.query(Utilisateur).get(id_user)
            if not user:
                return False, "Utilisateur introuvable."
            user.IsActive = not user.IsActive
            etat = "activé" if user.IsActive else "désactivé"
            session.commit()
            return True, f"Compte '{user.Login}' {etat}."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def set_printer_preference(id_user: int, printer_name: str | None) -> tuple[bool, str]:
        session = get_session()
        try:
            user = session.query(Utilisateur).get(id_user)
            if not user:
                return False, "Utilisateur introuvable."
            user.ImprimanteDefaut = printer_name or None
            session.commit()
            return True, "Préférence d'imprimante enregistrée."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete(id_user: int) -> tuple[bool, str]:
        from app.session import AppSession
        session = get_session()
        try:
            user = session.query(Utilisateur).get(id_user)
            if not user:
                return False, "Utilisateur introuvable."
            if user.IDUtilisateur == AppSession.get_current_user_id():
                return False, "Vous ne pouvez pas supprimer votre propre compte."
            login = user.Login
            session.delete(user)
            session.commit()
            return True, f"Utilisateur '{login}' supprimé avec succès !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {str(e)}"
        finally:
            session.close()
