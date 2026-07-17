from typing import List
from models.niveau import TNiveau
from models.cycle import TCycle
from app.database import get_session
import logging
logger = logging.getLogger(__name__)


class NiveauService:
    @staticmethod
    def get_cycles() -> List[TCycle]:
        """Recupere la liste des cycles pour la session active."""
        from app.session import AppSession
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            return session.query(TCycle).filter_by(
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).order_by(TCycle.Libelle.asc()).all()
        except Exception:
            logger.exception("Erreur recuperation cycles")
            return []
        finally:
            session.close()

    @staticmethod
    def get_all_with_cycle() -> list:
        """Recupere tous les niveaux avec les informations du cycle pour la session active."""
        from app.session import AppSession
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            niveaux = session.query(TNiveau).filter_by(
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).all()
            resultat = []
            for n in niveaux:
                resultat.append({
                    "IDT_Niveau": n.IDT_Niveau,
                    "Libelle": n.Libelle,
                    "CycleLibelle": n.cycle.Libelle if n.cycle else "Non defini",
                    "IDT_Cycle": n.IDT_Cycle
                })
            return resultat
        except Exception:
            logger.exception("Erreur recuperation niveaux")
            return []
        finally:
            session.close()

    @staticmethod
    def add_niveau(libelle: str, id_cycle: int) -> tuple[bool, str]:
        """Cree un nouveau niveau scolaire associe a un cycle."""
        if not libelle or not id_cycle:
            return False, "Le libelle du niveau et le cycle sont obligatoires."
            
        from app.session import AppSession
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            
            # Verifier les doublons pour le meme cycle, la meme annee scolaire et le meme etablissement
            exist = session.query(TNiveau).filter_by(
                Libelle=libelle.upper(),
                IDT_Cycle=id_cycle,
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).first()
            if exist:
                return False, f"Le niveau '{libelle}' existe deja pour ce cycle dans cette session active."

            # Creation du niveau
            nouveau = TNiveau(
                Libelle=libelle.upper(), 
                IDT_Cycle=id_cycle,
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            )
            session.add(nouveau)
            session.commit()
            return True, "Niveau enregistre avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_niveau(id_niveau: int) -> tuple[bool, str]:
        """Supprime un niveau."""
        from models.classe import TClasse
        from models.inscription import TInscription
        session = get_session()
        try:
            niveau = session.get(TNiveau, id_niveau)
            if niveau:
                # Verifier s'il y a des classes rattachees au niveau
                has_classes = session.query(TClasse).filter_by(IDT_Niveau=id_niveau).first() is not None
                if has_classes:
                    return False, "Impossible de supprimer ce niveau car il contient déjà des classes."

                # Verifier si des inscriptions referencent directement ce niveau
                # (TInscription.IDNiveau est en ON DELETE CASCADE)
                has_inscriptions = session.query(TInscription).filter_by(IDNiveau=id_niveau).first() is not None
                if has_inscriptions:
                    return False, "Impossible de supprimer ce niveau car il possede deja une inscription."

                session.delete(niveau)
                session.commit()
                return True, "Niveau supprime avec succes !"
            return False, "Niveau inexistant."
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer le niveau : {str(e)}"
        finally:
            session.close()
