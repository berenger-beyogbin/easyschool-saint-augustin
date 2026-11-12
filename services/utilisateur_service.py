import hashlib
import hmac
import os
import threading
import time
from datetime import datetime
from app.database import get_session
from models.utilisateur import Utilisateur
from models.profil import Profil
from sqlalchemy.orm import joinedload
from services.authorization import permission_denied


# ---------------------------------------------------------------------------
# Hachage des mots de passe (PBKDF2-SHA256, stdlib uniquement)
# ---------------------------------------------------------------------------

MIN_PASSWORD_LENGTH = 10
MAX_AUTH_FAILURES = 5
AUTH_LOCKOUT_SECONDS = 30
AUTH_FAILURE_MESSAGE = "Identifiant ou mot de passe incorrect."

_auth_failures: dict[str, tuple[int, float]] = {}
_auth_failures_lock = threading.Lock()


def _password_policy_error(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
    return None

def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"{salt}:{h.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
        return hmac.compare_digest(computed, bytes.fromhex(h))
    except (AttributeError, TypeError, ValueError):
        return False


_DUMMY_PASSWORD_HASH = _hash_password("mot-de-passe-factice")


def _is_auth_locked(login: str) -> bool:
    now = time.monotonic()
    with _auth_failures_lock:
        attempts, locked_until = _auth_failures.get(login, (0, 0.0))
        if locked_until > now:
            return True
        if locked_until:
            _auth_failures.pop(login, None)
        return False


def _record_auth_failure(login: str) -> None:
    now = time.monotonic()
    with _auth_failures_lock:
        attempts, locked_until = _auth_failures.get(login, (0, 0.0))
        if locked_until <= now:
            attempts += 1
            locked_until = now + AUTH_LOCKOUT_SECONDS if attempts >= MAX_AUTH_FAILURES else 0.0
        _auth_failures[login] = (attempts, locked_until)


def _clear_auth_failures(login: str) -> None:
    with _auth_failures_lock:
        _auth_failures.pop(login, None)


def _reset_auth_throttle() -> None:
    """Réinitialise le verrou local (principalement utile pour isoler les tests)."""
    with _auth_failures_lock:
        _auth_failures.clear()


class UtilisateurService:

    @staticmethod
    def has_any_user() -> bool:
        """Indique si au moins un utilisateur existe deja en base."""
        session = get_session()
        try:
            return session.query(Utilisateur).count() > 0
        finally:
            session.close()

    @staticmethod
    def get_admin_profil_id() -> int | None:
        """Recupere l'ID du profil ADMIN (seede par ProfilService.seed_default_profiles)."""
        session = get_session()
        try:
            admin_profil = session.query(Profil).filter_by(Code="ADMIN").first()
            return admin_profil.IDProfil if admin_profil else None
        finally:
            session.close()

    @staticmethod
    def create_first_admin(data: dict) -> tuple[bool, str]:
        """Cree le tout premier compte (profil ADMIN), avec le mot de passe choisi par l'utilisateur.

        Remplace l'ancien seeding automatique admin/admin123 : refuse de creer
        un compte si des utilisateurs existent deja, pour ne jamais servir de
        porte derobee une fois l'application deployee.
        """
        if UtilisateurService.has_any_user():
            return False, "Un compte existe deja : impossible de recreer le premier administrateur."
        id_profil = UtilisateurService.get_admin_profil_id()
        if not id_profil:
            return False, "Profil ADMIN introuvable (seeding des profils non effectue)."
        data = dict(data)
        data["IDProfil"] = id_profil
        data["IsActive"] = True
        return UtilisateurService.create(data, _bootstrap=True)

    @staticmethod
    def authenticate(login: str, password: str) -> tuple[bool, str, dict | None]:
        """
        Authentifie un utilisateur.
        Retourne (succès, message, user_data_dict) où user_data_dict contient
        les informations de session sans dépendance à la session SQLAlchemy.
        """
        normalized_login = login.strip()
        if _is_auth_locked(normalized_login):
            return False, AUTH_FAILURE_MESSAGE, None

        session = get_session()
        try:
            user = (
                session.query(Utilisateur)
                .options(joinedload(Utilisateur.profil))
                .filter_by(Login=normalized_login)
                .first()
            )
            if not user:
                # Effectue le même calcul coûteux que pour un compte existant afin
                # de limiter aussi l'énumération par mesure du temps de réponse.
                _verify_password(password, _DUMMY_PASSWORD_HASH)
                _record_auth_failure(normalized_login)
                return False, AUTH_FAILURE_MESSAGE, None
            password_matches = _verify_password(password, user.MotDePasseHash)
            if not user.IsActive or not password_matches:
                _record_auth_failure(normalized_login)
                return False, AUTH_FAILURE_MESSAGE, None

            _clear_auth_failures(normalized_login)
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
        except Exception:
            return False, "Connexion impossible. Veuillez réessayer.", None
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
    def create(data: dict, _bootstrap: bool = False) -> tuple[bool, str]:
        if not _bootstrap:
            denied = permission_denied("UTILISATEURS_MODIFIER", "créer un utilisateur")
            if denied:
                return denied
        session = get_session()
        try:
            login = data.get("Login", "").strip()
            nom = data.get("Nom", "").strip()
            password = data.get("Password", "")
            id_profil = data.get("IDProfil")

            if not login:
                return False, "Le login est obligatoire."
            if not nom:
                return False, "Le nom est obligatoire."
            if not password:
                return False, "Le mot de passe est obligatoire."
            policy_error = _password_policy_error(password)
            if policy_error:
                return False, policy_error
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
        denied = permission_denied("UTILISATEURS_MODIFIER", "modifier un utilisateur")
        if denied:
            return denied
        session = get_session()
        try:
            user = session.get(Utilisateur, id_user)
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

            new_pwd = data.get("Password", "")
            if new_pwd:
                policy_error = _password_policy_error(new_pwd)
                if policy_error:
                    return False, policy_error
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
        denied = permission_denied("UTILISATEURS_MODIFIER", "activer ou désactiver un utilisateur")
        if denied:
            return denied
        session = get_session()
        try:
            user = session.get(Utilisateur, id_user)
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
            user = session.get(Utilisateur, id_user)
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
        denied = permission_denied("UTILISATEURS_MODIFIER", "supprimer un utilisateur")
        if denied:
            return denied
        session = get_session()
        try:
            user = session.get(Utilisateur, id_user)
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
