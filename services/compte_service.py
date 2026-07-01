from typing import List, Optional, Tuple
from sqlalchemy import or_
from app.database import get_session
from models.compte import Compte
from models.type_sortie import TypeSortie
from models.sortie_fin import SortieFin

# Comptes de produits SYSCOA/OHADA créés automatiquement au démarrage
SYSCOA_INCOME_ACCOUNTS = {
    "7041": "SCOLARITE",
    "7042": "TRANSPORT",
    "7043": "CANTINE",
    "7044": "KIOSQUE",
}

class CompteService:
    @staticmethod
    def get_all_comptes() -> List[Compte]:
        """Recupere tous les comptes ordonnes par numero."""
        session = get_session()
        try:
            return session.query(Compte).order_by(Compte.NumCompte.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_comptes : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_compte_by_id(id_compte: int) -> Optional[Compte]:
        """Recupere un compte par son identifiant."""
        session = get_session()
        try:
            return session.query(Compte).filter_by(IDCompte=id_compte).first()
        except Exception as e:
            print(f"Erreur get_compte_by_id : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def search_comptes(search_text: str) -> List[Compte]:
        """Recherche dans les comptes par numero ou libelle."""
        session = get_session()
        try:
            if not search_text:
                return session.query(Compte).order_by(Compte.NumCompte.asc()).all()
            search_pattern = f"%{search_text}%"
            return session.query(Compte).filter(
                or_(
                    Compte.NumCompte.ilike(search_pattern),
                    Compte.LibCompte.ilike(search_pattern)
                )
            ).order_by(Compte.NumCompte.asc()).all()
        except Exception as e:
            print(f"Erreur search_comptes : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def create_compte(num_compte: str, lib_compte: str) -> Tuple[bool, str]:
        """Cree un nouveau compte."""
        if not num_compte or not num_compte.strip():
            return False, "Le numero de compte est obligatoire."
        if not lib_compte or not lib_compte.strip():
            return False, "Le libelle du compte est obligatoire."

        num_clean = num_compte.strip()
        lib_clean = lib_compte.strip()

        session = get_session()
        try:
            # Empecher les doublons NumCompte
            existing = session.query(Compte).filter(Compte.NumCompte.ilike(num_clean)).first()
            if existing:
                return False, f"Le compte numero '{num_clean}' existe deja."

            nouveau_compte = Compte(NumCompte=num_clean, LibCompte=lib_clean)
            session.add(nouveau_compte)
            session.commit()
            return True, "Compte cree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_compte(id_compte: int, num_compte: str, lib_compte: str) -> Tuple[bool, str]:
        """Met a jour un compte existant."""
        if not num_compte or not num_compte.strip():
            return False, "Le numero de compte est obligatoire."
        if not lib_compte or not lib_compte.strip():
            return False, "Le libelle du compte est obligatoire."

        num_clean = num_compte.strip()
        lib_clean = lib_compte.strip()

        session = get_session()
        try:
            compte = session.query(Compte).filter_by(IDCompte=id_compte).first()
            if not compte:
                return False, "Compte inexistant."

            # Empecher les doublons NumCompte
            existing = session.query(Compte).filter(Compte.NumCompte.ilike(num_clean), Compte.IDCompte != id_compte).first()
            if existing:
                return False, f"Le compte numero '{num_clean}' est deja utilise par un autre compte."

            compte.NumCompte = num_clean
            compte.LibCompte = lib_clean
            session.commit()
            return True, "Compte mis a jour avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def seed_comptes_syscoa() -> None:
        """Crée les comptes de produits SYSCOA (7041-7044) s'ils n'existent pas déjà."""
        session = get_session()
        try:
            for num, lib in SYSCOA_INCOME_ACCOUNTS.items():
                existing = session.query(Compte).filter(Compte.NumCompte == num).first()
                if not existing:
                    session.add(Compte(NumCompte=num, LibCompte=lib))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur seed_comptes_syscoa : {e}")
        finally:
            session.close()

    @staticmethod
    def delete_compte(id_compte: int) -> Tuple[bool, str]:
        """Supprime un compte s'il n'est pas utilise."""
        session = get_session()
        try:
            compte = session.query(Compte).filter_by(IDCompte=id_compte).first()
            if not compte:
                return False, "Compte inexistant."

            # Impossible de supprimer un compte deja utilise dans un mouvement financier (SortieFin)
            has_mouvement = session.query(SortieFin).filter_by(IDCompte=id_compte).first()
            if has_mouvement:
                return False, "Impossible de supprimer ce compte car il est associe a un ou plusieurs mouvements financiers."

            # ou un type de sortie (TypeSortie)
            has_type_sortie = session.query(TypeSortie).filter_by(IDCompte=id_compte).first()
            if has_type_sortie:
                return False, "Impossible de supprimer ce compte car il est utilise par un type de sortie."

            session.delete(compte)
            session.commit()
            return True, "Compte supprime avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur de suppression : {str(e)}"
        finally:
            session.close()
