from typing import List
from models.montant_autres_frais import MontantAutresFrais
from app.database import get_session
from sqlalchemy.orm import joinedload

class MontantAutresFraisService:
    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantAutresFrais]:
        """Recupere tous les tarifs d'autres frais pour une annee scolaire active."""
        session = get_session()
        try:
            return session.query(MontantAutresFrais).options(
                joinedload(MontantAutresFrais.niveau),
                joinedload(MontantAutresFrais.autre_frais)
            ).filter(MontantAutresFrais.IDAnneeScolaire == id_annee).all()
        except Exception as e:
            print(f"Erreur get_montants_by_annee MontantAutresFrais : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_montants_by_niveau(id_annee: int, id_niveau: int) -> List[MontantAutresFrais]:
        """Recupere tous les tarifs d'autres frais pour un niveau specifique."""
        session = get_session()
        try:
            return session.query(MontantAutresFrais).options(
                joinedload(MontantAutresFrais.autre_frais)
            ).filter(
                (MontantAutresFrais.IDAnneeScolaire == id_annee) & (MontantAutresFrais.IDT_Niveau == id_niveau)
            ).all()
        except Exception as e:
            print(f"Erreur get_montants_by_niveau MontantAutresFrais : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_montant_by_niveau_and_type(id_annee: int, id_niveau: int, id_autres_frais: int) -> MontantAutresFrais | None:
        """Recupere le tarif specifique d'un frais pour un niveau."""
        session = get_session()
        try:
            return session.query(MontantAutresFrais).filter(
                (MontantAutresFrais.IDAnneeScolaire == id_annee) &
                (MontantAutresFrais.IDT_Niveau == id_niveau) &
                (MontantAutresFrais.IDAutres_Frais == id_autres_frais)
            ).first()
        except Exception as e:
            print(f"Erreur get_montant_by_niveau_and_type MontantAutresFrais : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def save_montant_autres_frais(id_annee: int, id_niveau: int, id_autres_frais: int, montant: float, id_etab: int | None = None) -> tuple[bool, str]:
        """Cree ou met a jour le montant d'un autre frais."""
        if not id_annee or not id_niveau or not id_autres_frais:
            return False, "Annee scolaire, niveau et type de frais sont requis."

        session = get_session()
        try:
            m = session.query(MontantAutresFrais).filter(
                (MontantAutresFrais.IDAnneeScolaire == id_annee) &
                (MontantAutresFrais.IDT_Niveau == id_niveau) &
                (MontantAutresFrais.IDAutres_Frais == id_autres_frais)
            ).first()

            key = f"{id_annee}-{id_niveau}-{id_autres_frais}-{id_etab or 1}"

            if m:
                m.MontantFrais = montant
                m.IDEtablissement_Ecole = id_etab
                m.KeyCompose = key
            else:
                m = MontantAutresFrais(
                    IDAnneeScolaire=id_annee,
                    IDT_Niveau=id_niveau,
                    IDAutres_Frais=id_autres_frais,
                    MontantFrais=montant,
                    IDEtablissement_Ecole=id_etab,
                    KeyCompose=key
                )
                session.add(m)
            
            session.commit()
            return True, "Montant du frais annexe enregistre avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_montant_autres_frais(id_montant: int) -> tuple[bool, str]:
        """Supprime ou retire un montant d'autre frais."""
        session = get_session()
        try:
            m = session.query(MontantAutresFrais).get(id_montant)
            if not m:
                return False, "Tarif introuvable."
            session.delete(m)
            session.commit()
            return True, "Matière de frais retiree avec succes."
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
        finally:
            session.close()
