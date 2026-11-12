from typing import List
from models.montant_autres_frais import MontantAutresFrais
from app.database import get_session
from sqlalchemy.orm import joinedload
import logging
logger = logging.getLogger(__name__)


class MontantAutresFraisService:
    @staticmethod
    def ensure_frais_obligatoires(id_annee: int) -> tuple[bool, str]:
        """Initialise dans le catalogue les tarifs obligatoires encore absents."""
        from decimal import Decimal
        from models.annee_scolaire import TAnneeScolaire
        from models.autres_frais import AutresFrais
        from models.niveau import TNiveau

        tarifs = {
            "POLOS2": ("2 polos", Decimal("12000")),
            "TENUE_F2": ("2 polos et 2 jupes", Decimal("24000")),
            "FOUR_NOUV": ("Feuilles et classeur", Decimal("13000")),
            "FEUIL_ANC": ("Feuilles", Decimal("10000")),
        }
        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, id_annee)
            if not annee or annee.Libelle != "2026-2027":
                return True, "Aucun tarif obligatoire a initialiser."

            types = {f.CodeFrais: f for f in session.query(AutresFrais).filter(
                AutresFrais.CodeFrais.in_(tarifs)
            ).all()}
            for code, (libelle, _montant) in tarifs.items():
                if code not in types:
                    types[code] = AutresFrais(CodeFrais=code, LibelleFrais=libelle)
                    session.add(types[code])
            session.flush()

            niveaux = session.query(TNiveau).filter(TNiveau.IDAnneeScolaire == id_annee).all()
            existants = {
                (m.IDT_Niveau, m.IDAutres_Frais)
                for m in session.query(MontantAutresFrais).filter(
                    MontantAutresFrais.IDAnneeScolaire == id_annee,
                    MontantAutresFrais.IDAutres_Frais.in_(f.IDAutres_Frais for f in types.values()),
                ).all()
            }
            for niveau in niveaux:
                for code, (_libelle, montant) in tarifs.items():
                    frais = types[code]
                    if (niveau.IDT_Niveau, frais.IDAutres_Frais) in existants:
                        continue
                    session.add(MontantAutresFrais(
                        IDAnneeScolaire=id_annee,
                        IDT_Niveau=niveau.IDT_Niveau,
                        IDAutres_Frais=frais.IDAutres_Frais,
                        MontantFrais=montant,
                        IDEtablissement_Ecole=niveau.IDEtablissement_Ecole,
                        KeyCompose=f"{id_annee}-{niveau.IDT_Niveau}-{frais.IDAutres_Frais}-{niveau.IDEtablissement_Ecole or 1}",
                    ))
            session.commit()
            return True, "Tarifs obligatoires initialises."
        except Exception as e:
            session.rollback()
            logger.exception("Erreur d'initialisation des frais obligatoires")
            return False, f"Erreur d'initialisation : {e}"
        finally:
            session.close()

    @staticmethod
    def get_montants_by_annee(id_annee: int) -> List[MontantAutresFrais]:
        """Recupere tous les tarifs d'autres frais pour une annee scolaire active."""
        session = get_session()
        try:
            return session.query(MontantAutresFrais).options(
                joinedload(MontantAutresFrais.niveau),
                joinedload(MontantAutresFrais.autre_frais)
            ).filter(MontantAutresFrais.IDAnneeScolaire == id_annee).all()
        except Exception:
            logger.exception("Erreur get_montants_by_annee MontantAutresFrais")
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
        except Exception:
            logger.exception("Erreur get_montants_by_niveau MontantAutresFrais")
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
        except Exception:
            logger.exception("Erreur get_montant_by_niveau_and_type MontantAutresFrais")
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
            m = session.get(MontantAutresFrais, id_montant)
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
