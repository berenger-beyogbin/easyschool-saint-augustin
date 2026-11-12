from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.database import get_session
from models.audit_log import AuditLog
import logging
logger = logging.getLogger(__name__)



class AuditLogService:
    @staticmethod
    def log(
        action: str,
        table_cible: str,
        id_cible: int,
        id_utilisateur: Optional[int] = None,
        ancienne_valeur: Optional[str] = None,
        nouvelle_valeur: Optional[str] = None,
        motif: Optional[str] = None,
    ) -> None:
        """Enregistre une entree d'audit. Best-effort : une erreur ici ne doit
        jamais faire echouer l'operation metier qu'elle journalise (elle est
        toujours appelee apres le commit de cette derniere)."""
        session = get_session()
        try:
            session.add(AuditLog(
                IDUtilisateur=id_utilisateur,
                Action=action,
                TableCible=table_cible,
                IDCible=id_cible,
                AncienneValeur=ancienne_valeur,
                NouvelleValeur=nouvelle_valeur,
                Motif=motif,
            ))
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Erreur AuditLogService.log")
        finally:
            session.close()

    @staticmethod
    def get_by_cible(table_cible: str, id_cible: int) -> List[AuditLog]:
        session = get_session()
        try:
            return session.query(AuditLog).options(joinedload(AuditLog.utilisateur)).filter(
                AuditLog.TableCible == table_cible,
                AuditLog.IDCible == id_cible,
            ).order_by(AuditLog.DateAction.desc()).all()
        except Exception:
            logger.exception("Erreur AuditLogService.get_by_cible")
            return []
        finally:
            session.close()

    @staticmethod
    def get_recent(limit: int = 200) -> List[AuditLog]:
        session = get_session()
        try:
            return session.query(AuditLog).options(joinedload(AuditLog.utilisateur)).order_by(
                AuditLog.DateAction.desc()
            ).limit(limit).all()
        except Exception:
            logger.exception("Erreur AuditLogService.get_recent")
            return []
        finally:
            session.close()
