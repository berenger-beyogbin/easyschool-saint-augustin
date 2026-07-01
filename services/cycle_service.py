from typing import List
from models.cycle import TCycle
from app.database import get_session
from app.session import AppSession

class CycleService:
    @staticmethod
    def get_all() -> List[TCycle]:
        """Recupere la liste des cycles pour la session active."""
        session = get_session()
        try:
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()
            return session.query(TCycle).filter_by(
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).order_by(TCycle.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur get_all TCycle : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def add_cycle(libelle: str) -> tuple[bool, str]:
        """Cree un nouveau cycle scolaire."""
        if not libelle:
            return False, "Le libelle du cycle est obligatoire."

        session = get_session()
        try:
            # Obtenir l'annee active et l'etablissement actif
            active_annee_id = AppSession.get_active_annee_id()
            active_etab_id = AppSession.get_active_etab_id()

            # Verifier l'existence pour la meme annee scolaire et le meme etablissement
            exist = session.query(TCycle).filter_by(
                Libelle=libelle.upper(),
                IDAnneeScolaire=active_annee_id,
                IDEtablissement_Ecole=active_etab_id
            ).first()
            if exist:
                return False, f"Le cycle '{libelle}' existe deja pour l'annee scolaire active."

            nouveau = TCycle(
                Libelle=libelle.upper(),
                IDEtablissement_Ecole=active_etab_id,
                IDAnneeScolaire=active_annee_id
            )
            session.add(nouveau)
            session.commit()
            return True, "Cycle enregistre avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_cycle(id_cycle: int) -> tuple[bool, str]:
        """Supprime un cycle scolaire."""
        from models.niveau import TNiveau
        from models.classe import TClasse
        session = get_session()
        try:
            cycle = session.get(TCycle, id_cycle)
            if cycle:
                # Verifier d'abord s'il y a des niveaux rattaches
                has_niveaux = session.query(TNiveau).filter_by(IDT_Cycle=id_cycle).first() is not None
                # Verifier s'il y a des classes rattachees
                has_classes = session.query(TClasse).filter_by(IDT_Cycle=id_cycle).first() is not None
                
                if has_niveaux or has_classes:
                    return False, "Impossible de supprimer ce cycle car il contient déjà des niveaux ou des classes."

                session.delete(cycle)
                session.commit()
                return True, "Cycle supprime avec succes !"
            return False, "Cycle inexistant."
        except Exception as e:
            session.rollback()
            return False, f"Impossible de supprimer le cycle : {str(e)}"
        finally:
            session.close()
