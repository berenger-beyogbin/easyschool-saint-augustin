from typing import List
from models.montant_scol import MontantScol
from models.niveau import TNiveau
from app.database import get_session
from sqlalchemy.orm import joinedload
import logging
logger = logging.getLogger(__name__)


class MontantScolariteService:
    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantScol]:
        """Recupere tous les paramétrages de scolarite pour une annee scolaire."""
        session = get_session()
        try:
            return session.query(MontantScol).options(
                joinedload(MontantScol.niveau)
            ).filter(MontantScol.IDTAnneeScolaire == id_annee).all()
        except Exception:
            logger.exception("Erreur get_montants_by_annee MontantScol")
            return []
        finally:
            session.close()

    @staticmethod
    def get_montant_by_niveau(id_annee: int, id_niveau: int) -> MontantScol | None:
        """Recupere le paramétrage pour un niveau et une annee scolaire specifiques."""
        session = get_session()
        try:
            return session.query(MontantScol).filter(
                (MontantScol.IDTAnneeScolaire == id_annee) & (MontantScol.IDNiveau == id_niveau)
            ).first()
        except Exception:
            logger.exception("Erreur get_montant_by_niveau MontantScol")
            return None
        finally:
            session.close()

    @staticmethod
    def save_montant_scolarite(id_annee: int, id_niveau: int, montant_non_affecte: float, montant_affecte: float) -> tuple[bool, str]:
        """Cree ou met a jour les montants de scolarite (non affecte / affecte) d'un niveau."""
        if not id_annee or not id_niveau:
            return False, "Annee scolaire et niveau sont requis."

        session = get_session()
        try:
            m = session.query(MontantScol).filter(
                (MontantScol.IDTAnneeScolaire == id_annee) & (MontantScol.IDNiveau == id_niveau)
            ).first()

            if m:
                m.MontantNonAffecte = montant_non_affecte
                m.MontantAffecte = montant_affecte
            else:
                m = MontantScol(
                    IDTAnneeScolaire=id_annee,
                    IDNiveau=id_niveau,
                    MontantNonAffecte=montant_non_affecte,
                    MontantAffecte=montant_affecte,
                )
                session.add(m)
            session.commit()
            return True, "Frais de scolarite mis a jour !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def apply_common_amount_to_all_levels(id_annee: int, montant_non_affecte: float, montant_affecte: float) -> tuple[bool, str]:
        """Applique des valeurs communes de scolarité (non affecte / affecte) pour tous les niveaux de l'année scolaire active."""
        if not id_annee:
            return False, "Aucune annee scolaire active."

        session = get_session()
        try:
            # Recuperer les niveaux de cette annee scolaire
            niveaux = session.query(TNiveau).filter_by(IDAnneeScolaire=id_annee).all()
            if not niveaux:
                # Recuperer tout niveau (fallback)
                niveaux = session.query(TNiveau).all()

            for niv in niveaux:
                m = session.query(MontantScol).filter(
                    (MontantScol.IDTAnneeScolaire == id_annee) & (MontantScol.IDNiveau == niv.IDT_Niveau)
                ).first()

                if m:
                    m.MontantNonAffecte = montant_non_affecte
                    m.MontantAffecte = montant_affecte
                else:
                    m = MontantScol(
                        IDTAnneeScolaire=id_annee,
                        IDNiveau=niv.IDT_Niveau,
                        MontantNonAffecte=montant_non_affecte,
                        MontantAffecte=montant_affecte,
                    )
                    session.add(m)

            session.commit()
            return True, "Montant commun applique avec succes a tous les niveaux !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur d'application : {str(e)}"
        finally:
            session.close()
