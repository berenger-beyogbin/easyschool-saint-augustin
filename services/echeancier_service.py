from datetime import date
from typing import Any

from sqlalchemy.orm import joinedload

from app.database import get_session
from models.annee_scolaire import TAnneeScolaire
from models.echeance_paiement import EcheancePaiement
from models.inscription import TInscription
from services.versement_service import VersementService


class EcheancierService:
    SCOLARITE = "SCOLARITE"
    TRANSPORT = "TRANSPORT"
    CANTINE = "CANTINE"

    PRESCOLAIRE = "PRESCOLAIRE"
    NOUVEAU_PRIMAIRE = "NOUVEAU_PRIMAIRE"
    ANCIEN_PRIMAIRE = "ANCIEN_PRIMAIRE"
    TOUS = "TOUS"

    _OFFICIEL_2026_2027 = {
        (SCOLARITE, PRESCOLAIRE): [
            (1, "A l'inscription", None, 100000),
            (2, "2e versement", date(2026, 11, 30), 40000),
            (3, "3e versement", date(2026, 12, 31), 30000),
        ],
        (SCOLARITE, NOUVEAU_PRIMAIRE): [
            (1, "A l'inscription", None, 125000),
            (2, "2e versement", date(2026, 11, 30), 40000),
            (3, "3e versement", date(2026, 12, 31), 31000),
        ],
        (SCOLARITE, ANCIEN_PRIMAIRE): [
            (1, "A l'inscription", None, 115000),
            (2, "2e versement", date(2026, 11, 30), 40000),
            (3, "3e versement", date(2026, 12, 31), 31000),
        ],
        (TRANSPORT, TOUS): [
            (1, "A l'inscription", None, 50000),
            (2, "2e versement", date(2027, 1, 31), 40000),
            (3, "3e versement", date(2027, 3, 31), 30000),
        ],
        (CANTINE, TOUS): [
            (1, "A l'inscription", None, 50000),
            (2, "2e versement", date(2027, 1, 31), 40000),
            (3, "3e versement", date(2027, 3, 31), 30000),
        ],
    }

    @staticmethod
    def categorie_inscription(inscription: TInscription) -> str:
        code = VersementService._normaliser_libelle_niveau(
            inscription.niveau.Libelle if inscription.niveau else ""
        )
        if code in {"PS", "MS", "GS"}:
            return EcheancierService.PRESCOLAIRE
        return (
            EcheancierService.NOUVEAU_PRIMAIRE
            if inscription.Nouveau
            else EcheancierService.ANCIEN_PRIMAIRE
        )

    @staticmethod
    def _fallback(annee: TAnneeScolaire, type_frais: str, categorie: str) -> list[dict]:
        if not annee or annee.Libelle != "2026-2027":
            return []
        cle_categorie = categorie if type_frais == EcheancierService.SCOLARITE else EcheancierService.TOUS
        return [
            {
                "numero": numero,
                "libelle": libelle,
                "date_echeance": date_echeance,
                "montant": float(montant),
            }
            for numero, libelle, date_echeance, montant
            in EcheancierService._OFFICIEL_2026_2027.get((type_frais, cle_categorie), [])
        ]

    @staticmethod
    def get_tranches(id_annee: int, type_frais: str, categorie: str) -> list[dict]:
        session = get_session()
        try:
            annee = session.get(TAnneeScolaire, id_annee)
            cle_categorie = categorie if type_frais == EcheancierService.SCOLARITE else EcheancierService.TOUS
            lignes = session.query(EcheancePaiement).filter(
                EcheancePaiement.IDTAnneeScolaire == id_annee,
                EcheancePaiement.TypeFrais == type_frais,
                EcheancePaiement.Categorie == cle_categorie,
            ).order_by(EcheancePaiement.NumeroTranche).all()
            if not lignes:
                return EcheancierService._fallback(annee, type_frais, categorie)
            return [
                {
                    "numero": ligne.NumeroTranche,
                    "libelle": ligne.Libelle,
                    "date_echeance": ligne.DateEcheance,
                    "montant": float(ligne.Montant),
                }
                for ligne in lignes
            ]
        finally:
            session.close()

    @staticmethod
    def remplacer_tranches(
        id_annee: int, type_frais: str, categorie: str, tranches: list[dict]
    ) -> tuple[bool, str]:
        """Remplace atomiquement l'echeancier d'une categorie pour une annee."""
        from app.session import AppSession

        allowed, message = AppSession.require_permission("SCOLARITE_VERSEMENTS")
        if not allowed:
            return False, message
        if type_frais not in {
            EcheancierService.SCOLARITE,
            EcheancierService.TRANSPORT,
            EcheancierService.CANTINE,
        }:
            return False, "Type de frais invalide."
        if not tranches:
            return False, "Au moins une tranche est obligatoire."

        session = get_session()
        try:
            if not session.get(TAnneeScolaire, id_annee):
                return False, "Annee scolaire introuvable."
            session.query(EcheancePaiement).filter(
                EcheancePaiement.IDTAnneeScolaire == id_annee,
                EcheancePaiement.TypeFrais == type_frais,
                EcheancePaiement.Categorie == categorie,
            ).delete(synchronize_session=False)
            for index, tranche in enumerate(tranches, start=1):
                montant = float(tranche.get("montant", 0))
                if montant <= 0:
                    raise ValueError("Le montant de chaque tranche doit etre positif.")
                session.add(EcheancePaiement(
                    IDTAnneeScolaire=id_annee,
                    TypeFrais=type_frais,
                    Categorie=categorie,
                    NumeroTranche=int(tranche.get("numero", index)),
                    Libelle=(tranche.get("libelle") or f"Tranche {index}").strip(),
                    DateEcheance=tranche.get("date_echeance"),
                    Montant=montant,
                ))
            session.commit()
            return True, "Echeancier enregistre avec succes."
        except Exception as exc:
            session.rollback()
            return False, f"Echec de l'enregistrement de l'echeancier : {exc}"
        finally:
            session.close()

    @staticmethod
    def situation(
        tranches: list[dict], montant_paye: float, date_inscription: date,
        date_reference: date | None = None,
    ) -> dict[str, Any]:
        reference = date_reference or date.today()
        normalisees = []
        for tranche in tranches:
            item = dict(tranche)
            item["date_effective"] = item["date_echeance"] or date_inscription
            normalisees.append(item)
        normalisees.sort(key=lambda item: (item["date_effective"], item["numero"]))

        exigible = sum(item["montant"] for item in normalisees if item["date_effective"] <= reference)
        total = sum(item["montant"] for item in normalisees)
        reste_exigible = max(0.0, exigible - montant_paye)
        prochaine = next(
            (item for item in normalisees if item["date_effective"] > reference), None
        )
        impayee = next(
            (
                item for item in normalisees
                if sum(
                    t["montant"] for t in normalisees
                    if (t["date_effective"], t["numero"])
                    <= (item["date_effective"], item["numero"])
                ) > montant_paye
            ),
            None,
        )

        if reste_exigible > 0:
            statut = "EN RETARD"
        elif montant_paye >= total and total > 0:
            statut = "SOLDE"
        else:
            statut = "A JOUR"

        return {
            "statut": statut,
            "total_echeancier": total,
            "exigible": exigible,
            "paye": montant_paye,
            "reste_exigible": reste_exigible,
            "prochaine_echeance": prochaine,
            "tranche_impayee": impayee,
            "tranches": normalisees,
        }

    @staticmethod
    def get_situations_eleve(
        id_annee: int, id_eleve: int, montants_payes: dict[str, float],
        date_reference: date | None = None,
    ) -> dict[str, dict]:
        session = get_session()
        try:
            inscription = session.query(TInscription).options(
                joinedload(TInscription.niveau)
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                TInscription.IDEleve == id_eleve,
            ).first()
            if not inscription:
                return {}
            categorie = EcheancierService.categorie_inscription(inscription)
            date_inscription = inscription.DateInscription
        finally:
            session.close()

        resultat = {}
        for type_frais in (
            EcheancierService.SCOLARITE,
            EcheancierService.TRANSPORT,
            EcheancierService.CANTINE,
        ):
            if type_frais == EcheancierService.SCOLARITE and not inscription.Scolarite:
                continue
            if type_frais == EcheancierService.TRANSPORT and not inscription.Transport:
                continue
            if type_frais == EcheancierService.CANTINE and not inscription.Cantine:
                continue
            tranches = EcheancierService.get_tranches(id_annee, type_frais, categorie)
            if tranches:
                resultat[type_frais.lower()] = EcheancierService.situation(
                    tranches,
                    montants_payes.get(type_frais.lower(), 0.0),
                    date_inscription,
                    date_reference,
                )
        return resultat
