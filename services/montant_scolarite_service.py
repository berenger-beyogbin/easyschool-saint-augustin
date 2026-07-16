from typing import List
from models.montant_scol import MontantScol
from models.niveau import TNiveau
from app.database import get_session
from app.session import AppSession
from sqlalchemy.orm import joinedload

class MontantScolariteService:
    @staticmethod
    def _require_versements_permission() -> tuple[bool, str]:
        return AppSession.require_permission("SCOLARITE_VERSEMENTS")

    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantScol]:
        """Recupere tous les paramétrages de scolarite pour une annee scolaire."""
        session = get_session()
        try:
            return session.query(MontantScol).options(
                joinedload(MontantScol.niveau)
            ).filter(MontantScol.IDTAnneeScolaire == id_annee).all()
        except Exception as e:
            print(f"Erreur get_montants_by_annee MontantScol : {e}")
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
        except Exception as e:
            print(f"Erreur get_montant_by_niveau MontantScol : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def save_montant_scolarite(id_annee: int, id_niveau: int, montant: float, montant_pri: float, montant_sec: float) -> tuple[bool, str]:
        """Cree ou met a jour les montants scolaires d'un niveau."""
        if not id_annee or not id_niveau:
            return False, "Annee scolaire et niveau sont requis."
        allowed, msg = MontantScolariteService._require_versements_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            m = session.query(MontantScol).filter(
                (MontantScol.IDTAnneeScolaire == id_annee) & (MontantScol.IDNiveau == id_niveau)
            ).first()

            if m:
                m.Montant = montant
                m.MontantEnsPri = montant_pri
                m.MontantEnsSecondaire = montant_sec
            else:
                m = MontantScol(
                    IDTAnneeScolaire=id_annee,
                    IDNiveau=id_niveau,
                    Montant=montant,
                    MontantEnsPri=montant_pri,
                    MontantEnsSecondaire=montant_sec
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
    def apply_common_amount_to_all_levels(id_annee: int, montant: float, montant_pri: float, montant_sec: float) -> tuple[bool, str]:
        """Applique une valeur commune de scolarité pour tous les niveaux de l'année scolaire active."""
        if not id_annee:
            return False, "Aucune annee scolaire active."
        allowed, msg = MontantScolariteService._require_versements_permission()
        if not allowed:
            return False, msg

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
                    m.Montant = montant
                    m.MontantEnsPri = montant_pri
                    m.MontantEnsSecondaire = montant_sec
                else:
                    m = MontantScol(
                        IDTAnneeScolaire=id_annee,
                        IDNiveau=niv.IDT_Niveau,
                        Montant=montant,
                        MontantEnsPri=montant_pri,
                        MontantEnsSecondaire=montant_sec
                    )
                    session.add(m)

            session.commit()
            return True, "Montant commun applique avec succes a tous les niveaux !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur d'application : {str(e)}"
        finally:
            session.close()
