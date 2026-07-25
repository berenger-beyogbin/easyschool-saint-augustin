import re
import unicodedata
from typing import List, Dict, Any
from datetime import date
from sqlalchemy.orm import joinedload
from models.inscription import TInscription
from models.frais_examen_cm2 import MontantExamenCM2, VersementExamenCM2
from models.annee_scolaire import TAnneeScolaire
from app.database import get_session
from app.session import AppSession


class FraisExamenCM2Service:
    """Encaissement du frais d'examen CM2 : montant configurable par annee,
    paye en une seule fois par eleve."""

    @staticmethod
    def _normaliser_libelle_niveau(libelle: str | None) -> str:
        texte = unicodedata.normalize("NFKD", libelle or "")
        texte = "".join(car for car in texte if not unicodedata.combining(car))
        return re.sub(r"[^A-Z0-9]", "", texte.upper())

    @staticmethod
    def _require_permission() -> tuple[bool, str]:
        return AppSession.require_permission("EXAMEN_CM2_VIEW")

    # ─── Montant configure ──────────────────────────────────────────────────

    @staticmethod
    def get_montant_configure(id_annee: int) -> float:
        """Recupere le montant du frais d'examen CM2 configure pour l'annee."""
        if not id_annee:
            return 0.0
        session = get_session()
        try:
            m = session.query(MontantExamenCM2).filter(
                MontantExamenCM2.IDTAnneeScolaire == id_annee
            ).first()
            return float(m.Montant) if m else 0.0
        except Exception as e:
            print(f"Erreur get_montant_configure MontantExamenCM2 : {e}")
            return 0.0
        finally:
            session.close()

    @staticmethod
    def save_montant(id_annee: int, montant: float) -> tuple[bool, str]:
        """Cree ou met a jour le montant du frais d'examen CM2 pour l'annee."""
        if not id_annee:
            return False, "Aucune annee scolaire active."
        if montant < 0:
            return False, "Le montant ne peut pas etre negatif."
        allowed, msg = FraisExamenCM2Service._require_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            m = session.query(MontantExamenCM2).filter(
                MontantExamenCM2.IDTAnneeScolaire == id_annee
            ).first()
            if m:
                m.Montant = montant
            else:
                m = MontantExamenCM2(IDTAnneeScolaire=id_annee, Montant=montant)
                session.add(m)
            session.commit()
            return True, "Montant du frais d'examen CM2 mis a jour !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur base de donnees : {str(e)}"
        finally:
            session.close()

    # ─── Eleves de CM2 et situation financiere ──────────────────────────────

    @staticmethod
    def get_eleves_cm2(id_annee: int) -> List[Dict[str, Any]]:
        """Liste les eleves inscrits en CM2 pour l'annee, avec statut de paiement."""
        if not id_annee:
            return []
        session = get_session()
        try:
            inscriptions = session.query(TInscription).options(
                joinedload(TInscription.eleve),
                joinedload(TInscription.famille),
                joinedload(TInscription.classe),
                joinedload(TInscription.niveau),
            ).filter(TInscription.IDTAnneeScolaire == id_annee).all()

            cm2 = [
                ins for ins in inscriptions
                if ins.niveau and FraisExamenCM2Service._normaliser_libelle_niveau(ins.niveau.Libelle) == "CM2"
            ]

            versements = {
                v.IDEleve: v for v in session.query(VersementExamenCM2).filter(
                    VersementExamenCM2.IDTAnneeScolaire == id_annee
                ).all()
            }

            resultats = []
            for ins in cm2:
                v = versements.get(ins.IDEleve)
                resultats.append({
                    "id_eleve": ins.IDEleve,
                    "id_famille": ins.IDFamille,
                    "matricule": ins.eleve.Matricule if ins.eleve else "",
                    "nom": f"{ins.eleve.Nom} {ins.eleve.Prenoms}" if ins.eleve else "",
                    "classe": ins.classe.LibClasse if ins.classe else "",
                    "paye": v is not None,
                    "montant_paye": float(v.Montant) if v else 0.0,
                    "id_versement": v.IDVersementExamenCM2 if v else None,
                    "date_versement": v.DateVers if v else None,
                })
            resultats.sort(key=lambda r: r["nom"])
            return resultats
        except Exception as e:
            print(f"Erreur get_eleves_cm2 : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_versement_eleve(id_annee: int, id_eleve: int) -> VersementExamenCM2 | None:
        if not id_annee or not id_eleve:
            return None
        session = get_session()
        try:
            return session.query(VersementExamenCM2).filter(
                (VersementExamenCM2.IDTAnneeScolaire == id_annee) &
                (VersementExamenCM2.IDEleve == id_eleve)
            ).first()
        except Exception as e:
            print(f"Erreur get_versement_eleve : {e}")
            return None
        finally:
            session.close()

    # ─── Encaissement / annulation ──────────────────────────────────────────

    @staticmethod
    def create_versement(
        id_annee: int,
        id_eleve: int,
        id_famille: int,
        date_v: date,
        montant: float,
        login: str = "ADMIN",
    ) -> tuple[bool, str, int | None]:
        """Enregistre le versement unique du frais d'examen CM2 pour un eleve."""
        if not id_annee:
            return False, "Aucune annee scolaire active.", None
        if not id_eleve or not id_famille:
            return False, "Eleve et famille responsables sont obligatoires.", None
        if montant <= 0:
            return False, "Le montant encaisse doit etre superieur a 0 FCFA.", None
        allowed, msg = FraisExamenCM2Service._require_permission()
        if not allowed:
            return False, msg, None

        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, id_annee)
            if not annee:
                return False, "Annee scolaire introuvable.", None
            if annee.Cloturer:
                return False, "Impossible d'encaisser : l'annee scolaire active est cloturee.", None

            existant = session.query(VersementExamenCM2).filter(
                (VersementExamenCM2.IDTAnneeScolaire == id_annee) &
                (VersementExamenCM2.IDEleve == id_eleve)
            ).first()
            if existant:
                return False, "Le frais d'examen CM2 a deja ete encaisse pour cet eleve cette annee.", None

            n_vers = VersementExamenCM2(
                IDTAnneeScolaire=id_annee,
                IDEleve=id_eleve,
                IDFamille=id_famille,
                DateVers=date_v,
                Montant=montant,
                Login=login,
            )
            session.add(n_vers)
            session.commit()
            return True, "Frais d'examen CM2 encaisse avec succes !", n_vers.IDVersementExamenCM2
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement du versement : {str(e)}", None
        finally:
            session.close()

    @staticmethod
    def delete_versement(id_versement: int) -> tuple[bool, str]:
        """Annule un encaissement de frais d'examen CM2."""
        allowed, msg = FraisExamenCM2Service._require_permission()
        if not allowed:
            return False, msg

        session = get_session()
        try:
            v = session.get(VersementExamenCM2, id_versement)
            if not v:
                return False, "Versement introuvable."

            annee = session.get(TAnneeScolaire, v.IDTAnneeScolaire)
            if annee and annee.Cloturer:
                return False, "Impossible de supprimer un versement appartenant a une annee cloturee."

            session.delete(v)
            session.commit()
            return True, "Versement annule avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur : {e}"
        finally:
            session.close()
