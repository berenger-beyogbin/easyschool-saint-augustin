from typing import List, Optional, Tuple
from app.database import get_session
from app.session import AppSession
from models.type_sortie import TypeSortie
from models.sortie_fin import SortieFin

class TypeSortieService:
    @staticmethod
    def _require_saisie_permission() -> Tuple[bool, str]:
        return AppSession.require_permission("COMPTABILITE_SAISIE")

    @staticmethod
    def get_all_type_sorties() -> List[TypeSortie]:
        """Recupere tous les types de sorties."""
        session = get_session()
        try:
            return session.query(TypeSortie).order_by(TypeSortie.LibelleSortie.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_type_sorties : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_type_sortie_by_id(id_type_sortie: int) -> Optional[TypeSortie]:
        """Recupere un type de sortie par son id."""
        session = get_session()
        try:
            return session.query(TypeSortie).filter_by(IDTypeSortie=id_type_sortie).first()
        except Exception as e:
            print(f"Erreur get_type_sortie_by_id : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def get_type_sorties_by_compte(id_compte: int) -> List[TypeSortie]:
        """Recupere les types de sorties lies a un compte specifique."""
        session = get_session()
        try:
            return session.query(TypeSortie).filter_by(IDCompte=id_compte).order_by(TypeSortie.LibelleSortie.asc()).all()
        except Exception as e:
            print(f"Erreur get_type_sorties_by_compte : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def create_type_sortie(libelle_sortie: str, id_compte: int, sens: str) -> Tuple[bool, str]:
        """Cree un nouveau type de sortie."""
        if not libelle_sortie or not libelle_sortie.strip():
            return False, "Le libelle du type de sortie est obligatoire."
        if not id_compte:
            return False, "Le compte associe est obligatoire."
        if sens not in ["Debit", "Credit"]:
            return False, "Le sens doit etre 'Debit' ou 'Credit'."
        allowed, msg = TypeSortieService._require_saisie_permission()
        if not allowed:
            return False, msg

        lib_clean = libelle_sortie.strip()

        session = get_session()
        try:
            # LibelleSortie unique par compte
            existing = session.query(TypeSortie).filter(
                TypeSortie.LibelleSortie.ilike(lib_clean),
                TypeSortie.IDCompte == id_compte
            ).first()
            if existing:
                return False, f"Le libelle '{lib_clean}' existe deja pour ce compte."

            nouveau_type = TypeSortie(LibelleSortie=lib_clean, IDCompte=id_compte, Sens=sens)
            session.add(nouveau_type)
            session.commit()
            return True, "Type de sortie cree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_type_sortie(id_type_sortie: int, libelle_sortie: str, id_compte: int, sens: str) -> Tuple[bool, str]:
        """Met a jour un type de sortie existant."""
        if not libelle_sortie or not libelle_sortie.strip():
            return False, "Le libelle du type de sortie est obligatoire."
        if not id_compte:
            return False, "Le compte associe est obligatoire."
        if sens not in ["Debit", "Credit"]:
            return False, "Le sens doit etre 'Debit' ou 'Credit'."
        allowed, msg = TypeSortieService._require_saisie_permission()
        if not allowed:
            return False, msg

        lib_clean = libelle_sortie.strip()

        session = get_session()
        try:
            type_sortie = session.query(TypeSortie).filter_by(IDTypeSortie=id_type_sortie).first()
            if not type_sortie:
                return False, "Type de sortie inexistant."

            # LibelleSortie unique par compte
            existing = session.query(TypeSortie).filter(
                TypeSortie.LibelleSortie.ilike(lib_clean),
                TypeSortie.IDCompte == id_compte,
                TypeSortie.IDTypeSortie != id_type_sortie
            ).first()
            if existing:
                return False, f"Le libelle '{lib_clean}' existe deja pour ce compte."

            type_sortie.LibelleSortie = lib_clean
            type_sortie.IDCompte = id_compte
            type_sortie.Sens = sens
            session.commit()
            return True, "Type de sortie mis a jour avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_type_sortie(id_type_sortie: int) -> Tuple[bool, str]:
        """Supprime un type de sortie."""
        allowed, msg = TypeSortieService._require_saisie_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            type_sortie = session.query(TypeSortie).filter_by(IDTypeSortie=id_type_sortie).first()
            if not type_sortie:
                return False, "Type de sortie inexistant."

            # Impossible de supprimer un type de sortie s'il est utilise dans un mouvement (Wait! SortieFin does not directly refer to TypeSortie, but we filter or can support it if needed. Wait, does SortieFin refer to TypeSortie? No, SortieFin refers to IDCompte, other tables might. No, wait, if any rules say "empêcher la suppression si utilisé dans SortieFin", wait, SortieFin refers to IDCompte and DebitCredit. Let's make sure if there is any column or we check if there are SortieFin with this account and sens, or if we want to be safe, since they don't have direct FK link, we can check if there are movements using the same account and DebitCredit. But let's check if we need to do any check or just delete it.)
            # Wait, let's keep the check simple: if there are any SortieFin records with the same account and same DebitCredit, maybe or just general check. Or if SortieFin has no direct link, we're safe to delete it since we don't have IDTypeSortie in SortieFin columns specified in the prompt!
            # Wait! The table description for SortieFin doesn't have IDTypeSortie! It only has Benef, Detail, Montant, NumBenef, DateSortie, Login, CodeSortie, IDAnSco, DebitCredit, IDCompte. So there is no FK from SortieFin to TypeSortie.
            # So, we can just delete type_sortie or if they want to be safe, we just delete it directly or check if any SortieFin has same IDCompte. Let's just delete the type_sortie.

            session.delete(type_sortie)
            session.commit()
            return True, "Type de sortie supprime avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur de suppression : {str(e)}"
        finally:
            session.close()
