from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func

from app.database import get_session
from app.session import AppSession
from models.eleve import Eleve
from models.cantine_externe import CantineTarif, InscriptionCantine, VersementCantine
from services.authorization import permission_denied


MONTANT_DEFAUT = Decimal("50000")


class CantineExterneService:
    @staticmethod
    def ensure_tarif_annee(id_annee: int) -> CantineTarif:
        session = get_session()
        try:
            tarif = session.query(CantineTarif).filter_by(IDTAnneeScolaire=id_annee).first()
            if tarif:
                session.expunge(tarif)
                return tarif
            tarif = CantineTarif(IDTAnneeScolaire=id_annee, Montant=MONTANT_DEFAUT)
            session.add(tarif)
            session.commit()
            session.refresh(tarif)
            session.expunge(tarif)
            return tarif
        finally:
            session.close()

    @staticmethod
    def get_tarif(id_annee: int) -> Decimal:
        return CantineExterneService.ensure_tarif_annee(id_annee).Montant

    @staticmethod
    def update_tarif(id_annee: int, montant) -> tuple[bool, str]:
        denied = permission_denied("CANTINE_EXTERNE_PARAMETRES", "modifier le tarif de la cantine externe")
        if denied:
            return denied
        CantineExterneService.ensure_tarif_annee(id_annee)
        session = get_session()
        try:
            montant = Decimal(str(montant))
            if montant < 0:
                return False, "Le montant doit être positif."
            row = session.query(CantineTarif).filter_by(IDTAnneeScolaire=id_annee).first()
            row.Montant = montant
            session.commit()
            return True, "Tarif mis à jour. Il s'appliquera aux prochaines inscriptions."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def inscrire_externe(id_annee: int, donnees: dict) -> tuple[bool, str]:
        """Crée une identité (Eleve générique, hors base scolaire) puis l'inscription cantine."""
        denied = permission_denied("CANTINE_EXTERNE_ADMISSIONS", "inscrire un pensionnaire cantine")
        if denied:
            return denied
        nom = (donnees.get("nom") or "").strip().upper()
        prenoms = (donnees.get("prenoms") or "").strip()
        naissance = donnees.get("date_naissance")
        sexe = donnees.get("sexe")
        responsable = (donnees.get("responsable_nom") or "").strip()
        contact = (donnees.get("responsable_contact") or "").strip()
        if not all((nom, prenoms, naissance, sexe, responsable, contact)):
            return False, "Renseignez tous les champs obligatoires du pensionnaire cantine."
        if naissance > date.today():
            return False, "La date de naissance ne peut pas être dans le futur."

        montant_total = CantineExterneService.get_tarif(id_annee)
        session = get_session()
        try:
            prefix = f"CANT-EXT-{date.today().year}-"
            existants = [m for (m,) in session.query(Eleve.Matricule).filter(Eleve.Matricule.like(f"{prefix}%"))]
            numeros = []
            for matricule_existant in existants:
                try:
                    numeros.append(int(matricule_existant.rsplit("-", 1)[1]))
                except (ValueError, IndexError):
                    continue
            matricule = f"{prefix}{max(numeros, default=0) + 1:03d}"
            eleve = Eleve(
                Matricule=matricule, Nom=nom, Prenoms=prenoms,
                DateNaissance=naissance,
                LieuNaissance=(donnees.get("lieu_naissance") or "").strip() or None,
                Sexe=int(sexe), Habitation=(donnees.get("habitation") or "").strip() or None,
                NomUrgence=responsable, ContactUrgence=contact,
            )
            session.add(eleve)
            session.flush()
            row = InscriptionCantine(
                IDEleve=eleve.IDEleve, IDTAnneeScolaire=id_annee,
                MontantTotal=montant_total, DateInscription=date.today(),
                ResponsableNom=responsable, ResponsableContact=contact,
                Statut="EN_COURS", Login=AppSession.get_logged_in_username(),
            )
            session.add(row)
            session.commit()
            return True, f"Pensionnaire cantine inscrit sous le matricule {matricule}."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def get_pensionnaires(id_annee: int) -> list[dict]:
        session = get_session()
        try:
            rows = session.query(InscriptionCantine, Eleve).join(
                Eleve, InscriptionCantine.IDEleve == Eleve.IDEleve
            ).filter(
                InscriptionCantine.IDTAnneeScolaire == id_annee
            ).order_by(Eleve.Nom, Eleve.Prenoms).all()
            result = []
            for inscription, eleve in rows:
                verse = session.query(func.coalesce(func.sum(VersementCantine.Montant), 0)).filter(
                    VersementCantine.IDInscriptionCantine == inscription.IDInscriptionCantine,
                    VersementCantine.Annule.is_(False),
                ).scalar()
                result.append({
                    "id": inscription.IDInscriptionCantine, "matricule": eleve.Matricule,
                    "nom": f"{eleve.Nom} {eleve.Prenoms}",
                    "responsable": inscription.ResponsableNom or "",
                    "contact": inscription.ResponsableContact or "",
                    "statut": inscription.Statut,
                    "montant": float(inscription.MontantTotal), "verse": float(verse),
                    "reste": float(inscription.MontantTotal - verse),
                })
            return result
        finally:
            session.close()

    @staticmethod
    def verser(id_inscription_cantine: int, montant, mode: str = "ESPECES", reference: str = "") -> tuple[bool, str]:
        denied = permission_denied("CANTINE_EXTERNE_VERSEMENTS", "enregistrer un versement de cantine externe")
        if denied:
            return denied
        session = get_session()
        try:
            montant = Decimal(str(montant))
            row = session.get(InscriptionCantine, id_inscription_cantine)
            if not row or row.Statut in ("SORTIE", "SUSPENDU"):
                return False, "Inscription cantine invalide."
            deja = session.query(func.coalesce(func.sum(VersementCantine.Montant), 0)).filter_by(
                IDInscriptionCantine=id_inscription_cantine, Annule=False
            ).scalar()
            reste = row.MontantTotal - deja
            if montant <= 0:
                return False, "Le montant doit être supérieur à zéro."
            if montant > reste:
                return False, f"Le montant dépasse le reste à payer ({int(reste):,} FCFA).".replace(",", " ")
            numero = f"CANT-{datetime.now():%Y%m%d%H%M%S%f}"
            versement = VersementCantine(
                IDInscriptionCantine=id_inscription_cantine, NumeroRecu=numero,
                DateVersement=date.today(), Montant=montant,
                ModePaiement=mode.strip().upper() or "ESPECES",
                ReferencePaiement=reference.strip() or None,
                Login=AppSession.get_logged_in_username(),
            )
            session.add(versement)
            session.flush()
            if montant >= reste:
                row.Statut = "SOLDE"
            session.commit()
            return True, f"Versement enregistré. Reçu {numero}."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def get_versements(id_annee: int) -> list[dict]:
        session = get_session()
        try:
            rows = session.query(VersementCantine, InscriptionCantine, Eleve).join(
                InscriptionCantine, VersementCantine.IDInscriptionCantine == InscriptionCantine.IDInscriptionCantine
            ).join(Eleve, InscriptionCantine.IDEleve == Eleve.IDEleve).filter(
                InscriptionCantine.IDTAnneeScolaire == id_annee
            ).order_by(VersementCantine.DateVersement.desc(), VersementCantine.IDVersementCantine.desc()).all()
            return [{
                "id": v.IDVersementCantine, "recu": v.NumeroRecu, "date": v.DateVersement,
                "nom": f"{e.Nom} {e.Prenoms}", "montant": float(v.Montant),
                "mode": v.ModePaiement, "annule": v.Annule,
            } for v, _, e in rows]
        finally:
            session.close()

    @staticmethod
    def annuler_versement(id_versement: int, motif: str) -> tuple[bool, str]:
        denied = permission_denied("CANTINE_EXTERNE_VERSEMENTS", "annuler un versement de cantine externe")
        if denied:
            return denied
        if not motif or not motif.strip():
            return False, "Le motif d'annulation est obligatoire."
        session = get_session()
        try:
            versement = session.get(VersementCantine, id_versement)
            if not versement:
                return False, "Versement introuvable."
            if versement.Annule:
                return False, "Ce versement est déjà annulé."
            versement.annuler(motif.strip(), AppSession.get_logged_in_username())
            session.flush()

            row = session.get(InscriptionCantine, versement.IDInscriptionCantine)
            if row and row.Statut not in ("SUSPENDU", "SORTIE"):
                total_verse = session.query(func.coalesce(func.sum(VersementCantine.Montant), 0)).filter_by(
                    IDInscriptionCantine=row.IDInscriptionCantine, Annule=False
                ).scalar()
                row.Statut = "SOLDE" if total_verse >= row.MontantTotal else "EN_COURS"

            session.commit()
            return True, "Versement annulé avec traçabilité."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def dashboard(id_annee: int) -> dict:
        rows = CantineExterneService.get_pensionnaires(id_annee)
        return {
            "effectif": len(rows),
            "soldes": sum(r["statut"] == "SOLDE" for r in rows),
            "en_cours": sum(r["statut"] == "EN_COURS" for r in rows),
            "attendu": sum(r["montant"] for r in rows),
            "encaisse": sum(r["verse"] for r in rows),
            "reste": sum(r["reste"] for r in rows),
        }
