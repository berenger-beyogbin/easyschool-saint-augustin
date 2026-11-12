from typing import List, Optional
from decimal import Decimal
from sqlalchemy import func

from app.database import get_session
from app.session import AppSession
from models.inscription import TInscription
from models.inscription_autres_frais import InscriptionAutresFrais
from models.autres_frais import AutresFrais
from models.montant_autres_frais import MontantAutresFrais
from models.versement_autres_frais import VersementAutresFrais
from models.annee_scolaire import TAnneeScolaire
import logging
logger = logging.getLogger(__name__)

ANNEE_TARIFAIRE_CJGA = "2026-2027"
FRAIS_OBLIGATOIRES = {
    "POLOS2": ("2 polos", Decimal("12000")),
    "TENUE_F2": ("2 polos et 2 jupes", Decimal("24000")),
    "FOUR_NOUV": ("Feuilles et classeur", Decimal("13000")),
    "FEUIL_ANC": ("Feuilles", Decimal("10000")),
}



class InscriptionAutresFraisService:
    """
    Service dedie a la gestion des "autres frais" coches a l'inscription d'un eleve.
    La presence d'une ligne InscriptionAutresFrais pour une inscription vaut "coche" :
    il n'existe pas de champ booleen Coche.
    """

    @staticmethod
    def _codes_obligatoires(inscription: TInscription) -> tuple[str, ...]:
        if not inscription.Nouveau:
            return ("FEUIL_ANC",)
        sexe = inscription.eleve.Sexe if inscription.eleve else None
        return (("TENUE_F2" if sexe == 2 else "POLOS2"), "FOUR_NOUV")

    @staticmethod
    def get_frais_obligatoires_attendus(id_annee: int, nouveau: bool, sexe: int, id_niveau: int | None = None) -> List[dict]:
        """Retourne un apercu UI des frais obligatoires sans ecrire en base."""
        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, id_annee) if id_annee else None
            if not annee or annee.Libelle != ANNEE_TARIFAIRE_CJGA:
                return []
            codes = ("FEUIL_ANC",) if not nouveau else (
                ("TENUE_F2" if sexe == 2 else "POLOS2"), "FOUR_NOUV"
            )
            types = {f.CodeFrais: f for f in session.query(AutresFrais).filter(
                AutresFrais.CodeFrais.in_(codes)
            ).all()}
            montants = {}
            if id_niveau:
                for m in session.query(MontantAutresFrais).filter(
                    MontantAutresFrais.IDAnneeScolaire == id_annee,
                    MontantAutresFrais.IDT_Niveau == id_niveau,
                    MontantAutresFrais.IDAutres_Frais.in_(f.IDAutres_Frais for f in types.values()),
                ).all():
                    montants[m.IDAutres_Frais] = m
            return [
                {
                    "IDMontantAutres": None,
                    "CodeFrais": code,
                    "LibelleFrais": FRAIS_OBLIGATOIRES[code][0],
                    "MontantFrais": montants.get(types[code].IDAutres_Frais).MontantFrais
                    if code in types and types[code].IDAutres_Frais in montants
                    else FRAIS_OBLIGATOIRES[code][1],
                    "Obligatoire": True,
                }
                for code in codes
            ]
        finally:
            session.close()

    @staticmethod
    def synchroniser_frais_obligatoires_session(session, inscription: TInscription, login: Optional[str] = None) -> None:
        """Cree/actualise les frais CJGA obligatoires dans la transaction appelante.

        Une ligne deja payee est immuable. Un changement de profil qui devrait
        retirer ou modifier une telle ligne est refuse afin d'eviter toute
        reecriture de l'historique financier.
        """
        if not inscription.annee_scolaire or inscription.annee_scolaire.Libelle != ANNEE_TARIFAIRE_CJGA:
            return

        codes_attendus = set(InscriptionAutresFraisService._codes_obligatoires(inscription))
        types = {
            f.CodeFrais: f for f in session.query(AutresFrais).filter(
                AutresFrais.CodeFrais.in_(FRAIS_OBLIGATOIRES.keys())
            ).all()
        }
        for code, (libelle, _montant) in FRAIS_OBLIGATOIRES.items():
            if code not in types:
                types[code] = AutresFrais(CodeFrais=code, LibelleFrais=libelle)
                session.add(types[code])
        session.flush()

        lignes = session.query(InscriptionAutresFrais).filter(
            InscriptionAutresFrais.IDTInscription == inscription.IDTInscription,
            InscriptionAutresFrais.Obligatoire == True,
        ).all()
        par_code = {ligne.CodeFraisSnapshot: ligne for ligne in lignes}
        ids_lignes = [ligne.IDInscriptionAutresFrais for ligne in lignes]
        ids_payes = set()
        if ids_lignes:
            ids_payes = {
                row[0] for row in session.query(VersementAutresFrais.IDInscriptionAutresFrais).filter(
                    VersementAutresFrais.IDInscriptionAutresFrais.in_(ids_lignes)
                ).all()
            }

        for code, ligne in par_code.items():
            if code not in codes_attendus:
                if ligne.IDInscriptionAutresFrais in ids_payes:
                    raise ValueError(
                        f"Le frais obligatoire deja paye '{ligne.LibelleSnapshot or code}' ne peut pas etre remplace."
                    )
                session.delete(ligne)

        login_effectif = login or AppSession.get_logged_in_username()
        for code in codes_attendus:
            libelle, montant = FRAIS_OBLIGATOIRES[code]
            tarif = session.query(MontantAutresFrais).filter(
                MontantAutresFrais.IDAnneeScolaire == inscription.IDTAnneeScolaire,
                MontantAutresFrais.IDT_Niveau == inscription.IDNiveau,
                MontantAutresFrais.IDAutres_Frais == types[code].IDAutres_Frais,
            ).first()
            if tarif:
                montant = tarif.MontantFrais
            ligne = par_code.get(code)
            if ligne:
                if ligne.IDInscriptionAutresFrais in ids_payes and Decimal(ligne.MontantApplique) != montant:
                    raise ValueError(f"Le montant du frais deja paye '{libelle}' ne peut pas etre modifie.")
                if ligne.IDInscriptionAutresFrais not in ids_payes:
                    ligne.MontantApplique = montant
                    ligne.LibelleSnapshot = libelle
                    ligne.IDAutres_Frais = types[code].IDAutres_Frais
                continue
            session.add(InscriptionAutresFrais(
                IDTInscription=inscription.IDTInscription,
                IDAutres_Frais=types[code].IDAutres_Frais,
                IDMontantAutres=None,
                MontantApplique=montant,
                Obligatoire=True,
                Login=login_effectif,
                CodeFraisSnapshot=code,
                LibelleSnapshot=libelle,
            ))

        inscription.AutresFrais = True

    @staticmethod
    def get_frais_coches(id_inscription: int) -> List[dict]:
        """Retourne la liste des frais deja coches pour une inscription."""
        session = get_session()
        try:
            lignes = session.query(InscriptionAutresFrais).filter(
                InscriptionAutresFrais.IDTInscription == id_inscription
            ).all()

            return [
                {
                    "IDInscriptionAutresFrais": ligne.IDInscriptionAutresFrais,
                    "IDTInscription": ligne.IDTInscription,
                    "IDAutres_Frais": ligne.IDAutres_Frais,
                    "CodeFraisSnapshot": ligne.CodeFraisSnapshot,
                    "LibelleSnapshot": ligne.LibelleSnapshot,
                    "MontantApplique": ligne.MontantApplique,
                    "Obligatoire": ligne.Obligatoire,
                    "DateCreation": ligne.DateCreation,
                    "Login": ligne.Login,
                }
                for ligne in lignes
            ]
        except Exception:
            logger.exception("Erreur get_frais_coches InscriptionAutresFrais")
            return []
        finally:
            session.close()

    @staticmethod
    def get_frais_impayes(id_inscription: int) -> List[dict]:
        """
        Retourne les frais coches pour une inscription qui n'ont pas encore ete regles
        par un versement (aucune ligne VersementAutresFrais associee). Utilise a la caisse
        pour ne proposer que les frais restant a payer.
        """
        session = get_session()
        try:
            lignes = session.query(InscriptionAutresFrais).outerjoin(
                VersementAutresFrais,
                VersementAutresFrais.IDInscriptionAutresFrais == InscriptionAutresFrais.IDInscriptionAutresFrais
            ).filter(
                InscriptionAutresFrais.IDTInscription == id_inscription,
                VersementAutresFrais.IDVersementAutresFrais.is_(None)
            ).all()

            return [
                {
                    "IDInscriptionAutresFrais": ligne.IDInscriptionAutresFrais,
                    "IDTInscription": ligne.IDTInscription,
                    "IDAutres_Frais": ligne.IDAutres_Frais,
                    "CodeFraisSnapshot": ligne.CodeFraisSnapshot,
                    "LibelleSnapshot": ligne.LibelleSnapshot,
                    "MontantApplique": ligne.MontantApplique,
                    "Obligatoire": ligne.Obligatoire,
                    "DateCreation": ligne.DateCreation,
                    "Login": ligne.Login,
                }
                for ligne in lignes
            ]
        except Exception:
            logger.exception("Erreur get_frais_impayes InscriptionAutresFrais")
            return []
        finally:
            session.close()

    @staticmethod
    def calculer_total_frais_coches(id_inscription: int) -> Decimal:
        """Retourne la somme des MontantApplique des frais coches pour une inscription (0 si aucune ligne)."""
        session = get_session()
        try:
            total = session.query(
                func.coalesce(func.sum(InscriptionAutresFrais.MontantApplique), 0)
            ).filter(
                InscriptionAutresFrais.IDTInscription == id_inscription
            ).scalar()
            return total if total is not None else Decimal("0")
        except Exception:
            logger.exception("Erreur calculer_total_frais_coches InscriptionAutresFrais")
            return Decimal("0")
        finally:
            session.close()

    @staticmethod
    def get_frais_proposes(id_niveau: int, id_annee_scolaire: int) -> List[dict]:
        """
        Retourne les frais parametres dans MontantAutresFrais pour un niveau et une annee scolaire.
        NOTE: pas de filtrage par sexe pour l'instant, MontantAutresFrais ne porte pas cette
        dimension. Un filtrage sexe pourra etre ajoute plus tard si le modele evolue.
        """
        session = get_session()
        try:
            montants = session.query(MontantAutresFrais).join(
                AutresFrais, MontantAutresFrais.IDAutres_Frais == AutresFrais.IDAutres_Frais
            ).filter(
                MontantAutresFrais.IDT_Niveau == id_niveau,
                MontantAutresFrais.IDAnneeScolaire == id_annee_scolaire,
                ~AutresFrais.CodeFrais.in_(FRAIS_OBLIGATOIRES),
            ).all()

            return [
                {
                    "IDMontantAutres": m.IDMontantAutres,
                    "IDAutres_Frais": m.IDAutres_Frais,
                    "CodeFrais": m.autre_frais.CodeFrais if m.autre_frais else None,
                    "LibelleFrais": m.autre_frais.LibelleFrais if m.autre_frais else None,
                    "MontantFrais": m.MontantFrais,
                }
                for m in montants
            ]
        except Exception:
            logger.exception("Erreur get_frais_proposes InscriptionAutresFrais")
            return []
        finally:
            session.close()

    @staticmethod
    def set_frais_coches(id_inscription: int, ids_montant_autres: List[int], login: Optional[str] = None) -> tuple[bool, str]:
        """
        Synchronise les frais coches pour une inscription a partir d'une liste d'IDMontantAutres :
        - supprime les lignes qui ne sont plus cochees ;
        - conserve (sans recalcul) les lignes deja existantes ;
        - ajoute les lignes nouvellement cochees en figeant MontantApplique et les snapshots.
        """
        session = get_session()
        try:
            inscription = session.get(TInscription, id_inscription)
            if not inscription:
                return False, "Inscription introuvable."

            ids_demandes = list({i for i in (ids_montant_autres or []) if i})

            montants_catalogue = []
            if ids_demandes:
                montants_catalogue = session.query(MontantAutresFrais).filter(
                    MontantAutresFrais.IDMontantAutres.in_(ids_demandes)
                ).all()

                ids_trouves = {m.IDMontantAutres for m in montants_catalogue}
                ids_invalides = set(ids_demandes) - ids_trouves
                if ids_invalides:
                    return False, f"Tarif(s) introuvable(s) dans le catalogue : {sorted(ids_invalides)}."

            # Un seul frais coche par type (IDAutres_Frais) pour une meme inscription
            desired_par_frais = {}
            for m in montants_catalogue:
                if m.IDAutres_Frais in desired_par_frais:
                    return False, "Impossible de cocher deux fois le meme type de frais pour cette inscription."
                desired_par_frais[m.IDAutres_Frais] = m

            lignes_existantes = session.query(InscriptionAutresFrais).filter(
                InscriptionAutresFrais.IDTInscription == id_inscription,
                InscriptionAutresFrais.Obligatoire == False,
            ).all()
            existantes_par_frais = {ligne.IDAutres_Frais: ligne for ligne in lignes_existantes}

            login_effectif = login or AppSession.get_logged_in_username()

            # Suppression des frais decoches
            for id_autres_frais, ligne in existantes_par_frais.items():
                if id_autres_frais not in desired_par_frais:
                    deja_paye = session.query(VersementAutresFrais.IDVersementAutresFrais).filter(
                        VersementAutresFrais.IDInscriptionAutresFrais == ligne.IDInscriptionAutresFrais
                    ).first()
                    if deja_paye:
                        return False, (
                            f"Le frais deja paye '{ligne.LibelleSnapshot or ligne.CodeFraisSnapshot}' "
                            "ne peut pas etre retire de l'inscription."
                        )
                    session.delete(ligne)

            # Ajout des frais nouvellement coches (les existants sont conserves tels quels)
            for id_autres_frais, montant in desired_par_frais.items():
                if id_autres_frais in existantes_par_frais:
                    continue

                autre_frais = montant.autre_frais or session.get(AutresFrais, id_autres_frais)

                nouvelle_ligne = InscriptionAutresFrais(
                    IDTInscription=id_inscription,
                    IDAutres_Frais=id_autres_frais,
                    IDMontantAutres=montant.IDMontantAutres,
                    MontantApplique=montant.MontantFrais,
                    Obligatoire=False,
                    Login=login_effectif,
                    CodeFraisSnapshot=autre_frais.CodeFrais if autre_frais else None,
                    LibelleSnapshot=autre_frais.LibelleFrais if autre_frais else None,
                )
                session.add(nouvelle_ligne)

            session.commit()
            return True, "Frais coches enregistres avec succes."
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement des frais coches : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def clear_frais_coches(id_inscription: int) -> tuple[bool, str]:
        """Supprime tous les frais coches d'une inscription."""
        session = get_session()
        try:
            inscription = session.get(TInscription, id_inscription)
            if not inscription:
                return False, "Inscription introuvable."

            session.query(InscriptionAutresFrais).filter(
                InscriptionAutresFrais.IDTInscription == id_inscription,
                InscriptionAutresFrais.Obligatoire == False,
            ).delete(synchronize_session=False)

            session.commit()
            return True, "Frais coches supprimes avec succes."
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression des frais coches : {str(e)}"
        finally:
            session.close()
