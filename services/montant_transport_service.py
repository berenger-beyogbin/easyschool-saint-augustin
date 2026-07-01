from typing import List
from models.montant_transport import MontantTransport
from models.niveau import TNiveau
from app.database import get_session
from sqlalchemy.orm import joinedload

class MontantTransportService:
    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantTransport]:
        """Recupere tous les paramétrages de transport pour une annee scolaire."""
        session = get_session()
        try:
            return session.query(MontantTransport).options(
                joinedload(MontantTransport.niveau)
            ).filter(MontantTransport.IDTAnneeScolaire == id_annee).all()
        except Exception as e:
            print(f"Erreur get_montants_by_annee MontantTransport : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_montant_by_niveau(id_annee: int, id_niveau: int) -> MontantTransport | None:
        """Recupere le paramétrage pour un niveau et une annee scolaire specifiques."""
        session = get_session()
        try:
            return session.query(MontantTransport).filter(
                (MontantTransport.IDTAnneeScolaire == id_annee) & (MontantTransport.IDNiveau == id_niveau)
            ).first()
        except Exception as e:
            print(f"Erreur get_montant_by_niveau MontantTransport : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def save_montant_transport(id_annee: int, id_niveau: int, montant: float) -> tuple[bool, str]:
        """Cree ou met a jour le montant de transport d'un niveau."""
        if not id_annee or not id_niveau:
            return False, "Annee scolaire et niveau sont requis."

        session = get_session()
        try:
            m = session.query(MontantTransport).filter(
                (MontantTransport.IDTAnneeScolaire == id_annee) & (MontantTransport.IDNiveau == id_niveau)
            ).first()

            if m:
                m.Montant = montant
            else:
                m = MontantTransport(
                    IDTAnneeScolaire=id_annee,
                    IDNiveau=id_niveau,
                    Montant=montant
                )
                session.add(m)
            session.commit()
            return True, "Frais de transport mis a jour !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def apply_common_amount_to_all_levels(id_annee: int, montant: float) -> tuple[bool, str]:
        """Applique une valeur commune de transport pour tous les niveaux de l'année scolaire active."""
        if not id_annee:
            return False, "Aucune annee scolaire active."

        session = get_session()
        try:
            niveaux = session.query(TNiveau).filter_by(IDAnneeScolaire=id_annee).all()
            if not niveaux:
                niveaux = session.query(TNiveau).all()

            for niv in niveaux:
                m = session.query(MontantTransport).filter(
                    (MontantTransport.IDTAnneeScolaire == id_annee) & (MontantTransport.IDNiveau == niv.IDT_Niveau)
                ).first()

                if m:
                    m.Montant = montant
                else:
                    m = MontantTransport(
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
