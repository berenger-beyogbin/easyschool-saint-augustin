import os
from models.etablissement import EtablissementEcole
from models.annee_scolaire import TAnneeScolaire
from app.database import get_session

class AppSession:
    _active_annee_id = None
    _active_annee_libelle = None
    _active_etab_id = None

    # Données de l'utilisateur connecté
    _current_user_id: int | None = None
    _current_user_login: str | None = None
    _current_user_nom: str | None = None
    _current_user_profil_code: str | None = None
    _current_user_profil_libelle: str | None = None
    _current_user_is_admin: bool = False
    _current_user_permissions: set[str] = set()
    _current_user_imprimante: str | None = None

    # ------------------------------------------------------------------
    # Gestion de la session utilisateur
    # ------------------------------------------------------------------

    @classmethod
    def set_current_user(cls, user_data: dict, permissions: set[str]):
        """Stocke les informations de l'utilisateur authentifié."""
        cls._current_user_id = user_data.get("IDUtilisateur")
        cls._current_user_login = user_data.get("Login", "")
        nom = user_data.get("Nom", "")
        prenoms = user_data.get("Prenoms", "")
        cls._current_user_nom = f"{nom} {prenoms}".strip() if prenoms else nom
        cls._current_user_profil_code = user_data.get("ProfilCode", "")
        cls._current_user_profil_libelle = user_data.get("ProfilLibelle", "")
        cls._current_user_is_admin = user_data.get("IsAdmin", False)
        cls._current_user_permissions = permissions
        cls._current_user_imprimante = user_data.get("ImprimanteDefaut") or None

    @classmethod
    def get_current_user_id(cls) -> int | None:
        return cls._current_user_id

    @classmethod
    def get_current_user_nom(cls) -> str:
        return cls._current_user_nom or ""

    @classmethod
    def get_current_user_login(cls) -> str:
        return cls._current_user_login or ""

    @classmethod
    def get_current_user_profil_libelle(cls) -> str:
        return cls._current_user_profil_libelle or ""

    @classmethod
    def get_current_user_imprimante(cls) -> str | None:
        return cls._current_user_imprimante

    @classmethod
    def set_current_user_imprimante(cls, printer_name: str | None):
        cls._current_user_imprimante = printer_name or None

    @classmethod
    def has_permission(cls, code: str) -> bool:
        """Retourne True si l'utilisateur connecté dispose de la permission donnée."""
        if cls._current_user_is_admin:
            return True
        return code in cls._current_user_permissions

    @classmethod
    def require_permission(cls, code: str) -> tuple[bool, str]:
        """Valide une permission avant une action métier sensible."""
        if cls.has_permission(code):
            return True, ""
        return False, f"Accès refusé : droit requis '{code}'."

    @classmethod
    def clear_current_user(cls):
        """Réinitialise l'utilisateur courant (utile après déconnexion ou en tests)."""
        cls._current_user_id = None
        cls._current_user_login = None
        cls._current_user_nom = None
        cls._current_user_profil_code = None
        cls._current_user_profil_libelle = None
        cls._current_user_is_admin = False
        cls._current_user_permissions = set()
        cls._current_user_imprimante = None

    @classmethod
    def get_logged_in_username(cls) -> str:
        """Retourne le nom de l'utilisateur connecté (compatibilité auditabilité)."""
        return cls._current_user_nom or cls._current_user_login or "Système"

    @classmethod
    def get_active_annee_id(cls):
        if cls._active_annee_id is None or not cls.is_active_annee_valid():
            cls.initialize_session()
        return cls._active_annee_id

    @classmethod
    def get_active_annee_libelle(cls):
        if cls._active_annee_libelle is None or not cls.is_active_annee_valid():
            cls.initialize_session()
        return cls._active_annee_libelle

    @classmethod
    def set_active_annee(cls, annee_id, libelle):
        cls._active_annee_id = annee_id
        cls._active_annee_libelle = libelle
        print(f"Session active: Annee Scolaire mise a jour -> ID={annee_id}, Libelle={libelle}")

    @classmethod
    def get_active_etab_id(cls):
        if cls._active_etab_id is None:
            cls.initialize_session()
        return cls._active_etab_id

    @classmethod
    def is_active_annee_valid(cls) -> bool:
        """Verifie si l'annee active courante est valide et non cloturee en base de donnees."""
        if cls._active_annee_id is None:
            return False
        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, cls._active_annee_id)
            if annee and not annee.Cloturer:
                return True
            return False
        except Exception:
            return False
        finally:
            session.close()

    @classmethod
    def ensure_active_annee(cls, session) -> TAnneeScolaire:
        """S'assure qu'on a une annee valide non cloturee en base, sinon en cree une nouvelle ou la suivante."""
        annee = session.query(TAnneeScolaire).filter_by(Cloturer=False).order_by(TAnneeScolaire.Libelle.desc()).first()
        if not annee:
            # Aucune annee non cloturee. Voyons s'il y a au moins une annee cloturee.
            derniere_annee = session.query(TAnneeScolaire).order_by(TAnneeScolaire.Libelle.desc()).first()
            if not derniere_annee:
                # Aucune annee n'existe du tout -> on cree 2026-2027 par defaut
                annee = TAnneeScolaire(Libelle="2026-2027", Cloturer=False)
                session.add(annee)
                session.commit()
                session.refresh(annee)
                print("ensure_active_annee: Creation de la premiere annee par defaut: 2026-2027")
            else:
                # S'il y a des annees mais toutes sont cloturees, on cree la suivante
                import re
                dern_lib = derniere_annee.Libelle
                match = re.match(r"^(\d{4})-(\d{4})$", dern_lib)
                if match:
                    y1 = int(match.group(1))
                    y2 = int(match.group(2))
                    nouveau_lib = f"{y1 + 1}-{y2 + 1}"
                else:
                    nouveau_lib = "2026-2027"
                
                annee = TAnneeScolaire(Libelle=nouveau_lib, Cloturer=False)
                session.add(annee)
                session.commit()
                session.refresh(annee)
                print(f"ensure_active_annee: Creation de la prochaine annee active car toutes cloturees: {nouveau_lib}")
        return annee

    @classmethod
    def initialize_session(cls):
        # Ne re-initialiser et écraser que si nécessaire
        etab_already_valid = cls._active_etab_id is not None
        annee_already_valid = cls.is_active_annee_valid()

        if etab_already_valid and annee_already_valid:
            # Conserver la session active car elle est valide
            return

        session = get_session()
        try:
            # 1. Recuperer ou initialiser l'etablissement actif
            if not etab_already_valid:
                etab = session.query(EtablissementEcole).first()
                if etab:
                    cls._active_etab_id = etab.IDEtablissement_Ecole
                else:
                    from services.etablissement_service import EtablissementService
                    etab = EtablissementService.get_etablissement()
                    if etab:
                        cls._active_etab_id = etab.IDEtablissement_Ecole

            # 2. Recuperer ou initialiser l'annee scolaire active
            if not annee_already_valid:
                annee = cls.ensure_active_annee(session)
                if annee:
                    cls._active_annee_id = annee.IDTAnneeScolaire
                    cls._active_annee_libelle = annee.Libelle

            # 3. Validation finale de securite
            if cls._active_annee_id is None or cls._active_etab_id is None:
                raise Exception("Session impossible à initialiser : année scolaire active ou établissement actif introuvable.")

        except Exception as e:
            print(f"Erreur d'initialisation de la session : {e}")
            # On leve expressément l'exception pour bloquer le demarrage de MainWindow
            raise e
        finally:
            session.close()
