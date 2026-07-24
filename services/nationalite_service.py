from typing import List
from models.nationalite import TNationalite
from app.database import get_session
import logging
logger = logging.getLogger(__name__)


class NationaliteService:
    @staticmethod
    def get_all() -> List[TNationalite]:
        """Recupere toutes les nationalites."""
        session = get_session()
        try:
            return session.query(TNationalite).order_by(TNationalite.Nationalite.asc()).all()
        except Exception:
            logger.exception("Erreur get_all TNationalite")
            return []
        finally:
            session.close()

    @staticmethod
    def add_nationalite(libelle: str) -> tuple[bool, str]:
        """Cree une nouvelle nationalite (insensible a la casse et aux espaces)."""
        if not libelle:
            return False, "Le libelle de la nationalite est obligatoire."

        # Nettoyer et normaliser les espaces et mettre en majuscule
        lib_clean = " ".join(libelle.strip().split()).upper()

        session = get_session()
        try:
            # Verifier si elle existe deja
            exist = session.query(TNationalite).filter(TNationalite.Nationalite.ilike(lib_clean)).first()
            if exist:
                return False, f"La nationalite '{lib_clean}' existe deja (insensible a la casse et aux espaces)."

            nouvelle = TNationalite(Nationalite=lib_clean)
            session.add(nouvelle)
            session.commit()
            return True, "Nationalite enregistree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_nationalite(id_nat: int) -> tuple[bool, str]:
        """Supprime une nationalite."""
        session = get_session()
        try:
            nat = session.get(TNationalite, id_nat)
            if nat:
                session.delete(nat)
                session.commit()
                return True, "Nationalite supprimee avec succes !"
            return False, "Nationalite inexistante."
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer la nationalite : {str(e)}"
        finally:
            session.close()
