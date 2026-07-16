from typing import List
from models.montant_cantine import MontantCantine
from models.niveau import TNiveau
from app.database import get_session
from app.session import AppSession
from sqlalchemy.orm import joinedload

class MontantCantineService:
    @staticmethod
    def _require_versements_permission() -> tuple[bool, str]:
        return AppSession.require_permission("SCOLARITE_VERSEMENTS")

    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantCantine]:
        """Recupere tous les paramétrages de cantine pour une annee scolaire."""
        session = get_session()
        try:
            return session.query(MontantCantine).options(
                joinedload(MontantCantine.niveau)
            ).filter(MontantCantine.IDTAnneeScolaire == id_annee).all()
        except Exception as e:
            print(f"Erreur get_montants_by_annee MontantCantine : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_montant_by_niveau(id_annee: int, id_niveau: int) -> MontantCantine | None:
        """Recupere le paramétrage pour un niveau et une annee scolaire specifiques."""
        session = get_session()
        try:
            return session.query(MontantCantine).filter(
                (MontantCantine.IDTAnneeScolaire == id_annee) & (MontantCantine.IDNiveau == id_niveau)
            ).first()
        except Exception as e:
            print(f"Erreur get_montant_by_niveau MontantCantine : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def save_montant_cantine(id_annee: int, id_niveau: int, montant: float) -> tuple[bool, str]:
        """Cree ou met a jour le montant de cantine d'un niveau."""
        if not id_annee or not id_niveau:
            return False, "Annee scolaire et niveau sont requis."
        allowed, msg = MontantCantineService._require_versements_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            m = session.query(MontantCantine).filter(
                (MontantCantine.IDTAnneeScolaire == id_annee) & (MontantCantine.IDNiveau == id_niveau)
            ).first()

            if m:
                m.Montant = montant
            else:
                m = MontantCantine(
                    IDTAnneeScolaire=id_annee,
                    IDNiveau=id_niveau,
                    Montant=montant
                )
                session.add(m)
            session.commit()
            return True, "Frais de cantine mis a jour !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def apply_common_amount_to_all_levels(id_annee: int, montant: float) -> tuple[bool, str]:
        """Applique une valeur commune de cantine pour tous les niveaux de l'année scolaire active."""
        if not id_annee:
            return False, "Aucune annee scolaire active."
        allowed, msg = MontantCantineService._require_versements_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            niveaux = session.query(TNiveau).filter_by(IDAnneeScolaire=id_annee).all()
            if not niveaux:
                niveaux = session.query(TNiveau).all()

            for niv in niveaux:
                m = session.query(MontantCantine).filter(
                    (MontantCantine.IDTAnneeScolaire == id_annee) & (MontantCantine.IDNiveau == niv.IDT_Niveau)
                ).first()

                if m:
                    m.Montant = montant
                else:
                    m = MontantCantine(
                        IDTAnneeScolaire=id_annee,
                        IDNiveau=niv.IDT_Niveau,
                        Montant=montant
                    )
                    session.add(m)

            session.commit()
            return True, "Montant commun applique avec succes a tous les niveaux !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur d'application : {str(e)}"
        finally:
            session.close()
