from typing import List
from models.religion import TReligion
from app.database import get_session
from app.session import AppSession

class ReligionService:
    @staticmethod
    def get_all() -> List[TReligion]:
        """Recupere toutes les religions."""
        session = get_session()
        try:
            return session.query(TReligion).order_by(TReligion.Religion.asc()).all()
        except Exception as e:
            print(f"Erreur get_all TReligion : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def add_religion(libelle: str) -> tuple[bool, str]:
        """Cree une nouvelle religion (insensible a la casse et aux espaces)."""
        allowed, msg = AppSession.require_permission("PARAMETRES_MODIFIER")
        if not allowed:
            return False, msg

        if not libelle:
            return False, "Le libelle de la religion est obligatoire."

        # Nettoyer et normaliser les espaces et mettre en majuscule
        lib_clean = " ".join(libelle.strip().split()).upper()

        session = get_session()
        try:
            # Verifier si elle existe deja
            exist = session.query(TReligion).filter(TReligion.Religion.ilike(lib_clean)).first()
            if exist:
                return False, f"La religion '{lib_clean}' existe deja (insensible a la casse et aux espaces)."

            nouvelle = TReligion(Religion=lib_clean)
            session.add(nouvelle)
            session.commit()
            return True, "Religion enregistree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_religion(id_rel: int) -> tuple[bool, str]:
        """Supprime une religion."""
        allowed, msg = AppSession.require_permission("PARAMETRES_MODIFIER")
        if not allowed:
            return False, msg

        session = get_session()
        try:
            rel = session.get(TReligion, id_rel)
            if rel:
                session.delete(rel)
                session.commit()
                return True, "Religion supprimee avec succes !"
            return False, "Religion inexistante."
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer la religion : {str(e)}"
        finally:
            session.close()
