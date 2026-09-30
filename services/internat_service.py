from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.database import get_session
from app.session import AppSession
from models.eleve import Eleve
from models.inscription import TInscription
from models.internat import (
    InscriptionInternat, InternatEcheance, InternatPieceDossier, VersementInternat,
)
from services.authorization import permission_denied


PIECES_DOSSIER = (
    ("EXTRAIT", "Photocopies de l'extrait de naissance", 2, True),
    ("PHOTOS", "Photos d'identité", 2, True),
    ("VACCINATION", "Certificat de vaccination à jour", 1, True),
    ("BULLETIN", "Photocopie du bulletin de l'année précédente", 1, True),
    ("DOSSIER", "Dossier d'inscription rempli", 1, True),
    ("REGLEMENT", "Règlement intérieur lu et signé", 1, True),
)

ECHEANCES_DEFAUT = (
    ("RESERVATION", "Réservation", 1, 200_000, 200_000),
    ("NOVEMBRE", "Mois de novembre", 2, 100_000, 100_000),
    ("JANVIER", "Mois de janvier", 3, 100_000, 100_000),
    ("FEVRIER", "Mois de février", 4, 50_000, 20_000),
)


class InternatService:
    @staticmethod
    def ensure_default_echeances(id_annee: int) -> None:
        session = get_session()
        try:
            if session.query(InternatEcheance).filter_by(IDTAnneeScolaire=id_annee).count():
                return
            for code, libelle, ordre, nouvelle, ancienne in ECHEANCES_DEFAUT:
                session.add(InternatEcheance(
                    IDTAnneeScolaire=id_annee, Code=code, Libelle=libelle,
                    Ordre=ordre, MontantNouvelle=nouvelle, MontantAncienne=ancienne,
                ))
            session.commit()
        finally:
            session.close()

    @staticmethod
    def get_echeances(id_annee: int) -> list[InternatEcheance]:
        InternatService.ensure_default_echeances(id_annee)
        session = get_session()
        try:
            rows = session.query(InternatEcheance).filter_by(IDTAnneeScolaire=id_annee).order_by(InternatEcheance.Ordre).all()
            for row in rows:
                session.expunge(row)
            return rows
        finally:
            session.close()

    @staticmethod
    def update_echeance(id_echeance: int, nouvelle, ancienne, date_limite=None) -> tuple[bool, str]:
        denied = permission_denied("INTERNAT_PARAMETRES", "modifier les tarifs de l'internat")
        if denied:
            return denied
        session = get_session()
        try:
            row = session.get(InternatEcheance, id_echeance)
            if not row:
                return False, "Échéance introuvable."
            nouvelle, ancienne = Decimal(str(nouvelle)), Decimal(str(ancienne))
            if nouvelle < 0 or ancienne < 0:
                return False, "Les montants doivent être positifs."
            row.MontantNouvelle, row.MontantAncienne = nouvelle, ancienne
            row.DateLimite = date_limite
            session.commit()
            return True, "Tarif mis à jour."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def get_eleves_eligibles(id_annee: int) -> list[dict]:
        session = get_session()
        try:
            rows = session.query(TInscription, Eleve).join(Eleve, TInscription.IDEleve == Eleve.IDEleve).outerjoin(
                InscriptionInternat, InscriptionInternat.IDTInscription == TInscription.IDTInscription
            ).filter(
                TInscription.IDTAnneeScolaire == id_annee,
                Eleve.Sexe == 2,
                InscriptionInternat.IDInscriptionInternat.is_(None),
            ).order_by(Eleve.Nom, Eleve.Prenoms).all()
            return [{"id_inscription": ins.IDTInscription, "nom": f"{el.Nom} {el.Prenoms}", "matricule": el.Matricule} for ins, el in rows]
        finally:
            session.close()

    @staticmethod
    def inscrire(id_inscription: int, type_pensionnaire: str, date_debut: date | None = None) -> tuple[bool, str]:
        denied = permission_denied("INTERNAT_ADMISSIONS", "inscrire une pensionnaire")
        if denied:
            return denied
        type_pensionnaire = type_pensionnaire.strip().upper()
        if type_pensionnaire not in {"NOUVELLE", "ANCIENNE"}:
            return False, "Type de pensionnaire invalide."
        session = get_session()
        try:
            ins = session.query(TInscription).options(joinedload(TInscription.eleve)).filter_by(IDTInscription=id_inscription).first()
            if not ins:
                return False, "Inscription scolaire introuvable."
            if ins.eleve.Sexe != 2:
                return False, "L'internat d'Attinguié est réservé aux filles."
            if session.query(InscriptionInternat).filter_by(IDTInscription=id_inscription).first():
                return False, "Cette élève est déjà inscrite à l'internat pour cette année."
            InternatService.ensure_default_echeances(ins.IDTAnneeScolaire)
            tarifs = session.query(InternatEcheance).filter_by(IDTAnneeScolaire=ins.IDTAnneeScolaire, Actif=True).all()
            total = sum((e.MontantNouvelle if type_pensionnaire == "NOUVELLE" else e.MontantAncienne) for e in tarifs)
            row = InscriptionInternat(
                IDTInscription=id_inscription, IDEleve=ins.IDEleve,
                IDTAnneeScolaire=ins.IDTAnneeScolaire, OrigineScolaire="COLLEGE",
                TypePensionnaire=type_pensionnaire,
                DateAdmission=date.today(), DateDebutPension=date_debut or date.today(),
                MontantAnnuel=total, Statut="DOSSIER_INCOMPLET",
                Login=AppSession.get_logged_in_username(),
            )
            session.add(row)
            session.flush()
            for code, libelle, qte, obligatoire in PIECES_DOSSIER:
                session.add(InternatPieceDossier(
                    IDInscriptionInternat=row.IDInscriptionInternat, CodePiece=code,
                    Libelle=libelle, QuantiteDemandee=qte, Obligatoire=obligatoire,
                ))
            session.commit()
            return True, "Pensionnaire inscrite. Le dossier est à compléter."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def inscrire_externe(id_annee: int, donnees: dict, type_pensionnaire: str,
                         date_debut: date | None = None) -> tuple[bool, str]:
        """Crée une identité sans inscription scolaire, puis l'admission à l'internat."""
        denied = permission_denied("INTERNAT_ADMISSIONS", "inscrire une pensionnaire externe")
        if denied:
            return denied
        type_pensionnaire = (type_pensionnaire or "").strip().upper()
        if type_pensionnaire not in {"NOUVELLE", "ANCIENNE"}:
            return False, "Type de pensionnaire invalide."
        nom = (donnees.get("nom") or "").strip().upper()
        prenoms = (donnees.get("prenoms") or "").strip()
        naissance = donnees.get("date_naissance")
        ecole = (donnees.get("etablissement") or "").strip()
        classe = (donnees.get("classe") or "").strip()
        responsable = (donnees.get("responsable_nom") or "").strip()
        contact = (donnees.get("responsable_contact") or "").strip()
        if not all((nom, prenoms, naissance, ecole, classe, responsable, contact)):
            return False, "Renseignez tous les champs obligatoires de la pensionnaire externe."
        if naissance > date.today():
            return False, "La date de naissance ne peut pas être dans le futur."

        InternatService.ensure_default_echeances(id_annee)
        session = get_session()
        try:
            prefix = f"INT-EXT-{date.today().year}-"
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
                Sexe=2, Habitation=(donnees.get("habitation") or "").strip() or None,
                NomUrgence=responsable, ContactUrgence=contact,
                EtablissementOrigine=ecole, ClasseSuivieOrigine=classe,
            )
            session.add(eleve)
            session.flush()
            tarifs = session.query(InternatEcheance).filter_by(IDTAnneeScolaire=id_annee, Actif=True).all()
            total = sum((e.MontantNouvelle if type_pensionnaire == "NOUVELLE" else e.MontantAncienne) for e in tarifs)
            row = InscriptionInternat(
                IDTInscription=None, IDEleve=eleve.IDEleve, IDTAnneeScolaire=id_annee,
                OrigineScolaire="EXTERNE", EtablissementFrequente=ecole,
                ClasseFrequentee=classe, ResponsableNom=responsable,
                ResponsableContact=contact, TypePensionnaire=type_pensionnaire,
                DateAdmission=date.today(), DateDebutPension=date_debut or date.today(),
                MontantAnnuel=total, Statut="DOSSIER_INCOMPLET",
                Login=AppSession.get_logged_in_username(),
            )
            session.add(row)
            session.flush()
            for code, libelle, qte, obligatoire in PIECES_DOSSIER:
                session.add(InternatPieceDossier(
                    IDInscriptionInternat=row.IDInscriptionInternat, CodePiece=code,
                    Libelle=libelle, QuantiteDemandee=qte, Obligatoire=obligatoire,
                ))
            session.commit()
            return True, f"Pensionnaire externe inscrite sous le matricule {matricule}. Le dossier est à compléter."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def get_pensionnaires(id_annee: int) -> list[dict]:
        session = get_session()
        try:
            rows = session.query(InscriptionInternat, Eleve).join(
                Eleve, InscriptionInternat.IDEleve == Eleve.IDEleve
            ).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee
            ).order_by(Eleve.Nom, Eleve.Prenoms).all()
            result = []
            for internat, eleve in rows:
                verse = session.query(func.coalesce(func.sum(VersementInternat.Montant), 0)).filter(
                    VersementInternat.IDInscriptionInternat == internat.IDInscriptionInternat,
                    VersementInternat.Annule.is_(False),
                ).scalar()
                pieces_total = session.query(InternatPieceDossier).filter_by(IDInscriptionInternat=internat.IDInscriptionInternat, Obligatoire=True).count()
                pieces_ok = session.query(InternatPieceDossier).filter(
                    InternatPieceDossier.IDInscriptionInternat == internat.IDInscriptionInternat,
                    InternatPieceDossier.Obligatoire.is_(True),
                    InternatPieceDossier.QuantiteRecue >= InternatPieceDossier.QuantiteDemandee,
                ).count()
                result.append({
                    "id": internat.IDInscriptionInternat, "matricule": eleve.Matricule,
                    "nom": f"{eleve.Nom} {eleve.Prenoms}", "type": internat.TypePensionnaire,
                    "origine": internat.OrigineScolaire,
                    "etablissement": internat.EtablissementFrequente or "",
                    "classe_externe": internat.ClasseFrequentee or "",
                    "statut": internat.Statut, "dossier": f"{pieces_ok}/{pieces_total}",
                    "montant": float(internat.MontantAnnuel), "verse": float(verse),
                    "reste": float(internat.MontantAnnuel - verse),
                })
            return result
        finally:
            session.close()

    @staticmethod
    def get_pieces(id_internat: int) -> list[dict]:
        session = get_session()
        try:
            rows = session.query(InternatPieceDossier).filter_by(IDInscriptionInternat=id_internat).order_by(InternatPieceDossier.IDPieceDossier).all()
            return [{"id": p.IDPieceDossier, "libelle": p.Libelle, "demandee": p.QuantiteDemandee, "recue": p.QuantiteRecue, "obligatoire": p.Obligatoire} for p in rows]
        finally:
            session.close()

    @staticmethod
    def enregistrer_dossier(id_internat: int, quantites: dict[int, int]) -> tuple[bool, str]:
        denied = permission_denied("INTERNAT_ADMISSIONS", "valider le dossier d'internat")
        if denied:
            return denied
        session = get_session()
        try:
            row = session.get(InscriptionInternat, id_internat)
            if not row:
                return False, "Pensionnaire introuvable."
            for piece in session.query(InternatPieceDossier).filter_by(IDInscriptionInternat=id_internat):
                qte = max(0, int(quantites.get(piece.IDPieceDossier, piece.QuantiteRecue)))
                piece.QuantiteRecue = qte
                piece.DateReception = date.today() if qte else None
                piece.VerifiePar = AppSession.get_logged_in_username() if qte else None
            session.flush()
            complet = all(p.QuantiteRecue >= p.QuantiteDemandee for p in row.pieces if p.Obligatoire)
            total_verse = session.query(func.coalesce(func.sum(VersementInternat.Montant), 0)).filter_by(IDInscriptionInternat=id_internat, Annule=False).scalar()
            row.Statut = "ADMISE" if complet and total_verse > 0 else ("EN_ATTENTE_PAIEMENT" if complet else "DOSSIER_INCOMPLET")
            session.commit()
            return True, "Dossier mis à jour."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def verser(id_internat: int, montant, mode: str = "ESPECES", reference: str = "",
              date_versement: date | None = None) -> tuple[bool, str]:
        denied = permission_denied("INTERNAT_VERSEMENTS", "enregistrer un versement d'internat")
        if denied:
            return denied
        session = get_session()
        try:
            montant = Decimal(str(montant))
            row = session.get(InscriptionInternat, id_internat)
            if not row or row.Statut == "SORTIE":
                return False, "Inscription d'internat invalide."
            deja = session.query(func.coalesce(func.sum(VersementInternat.Montant), 0)).filter_by(IDInscriptionInternat=id_internat, Annule=False).scalar()
            reste = row.MontantAnnuel - deja
            if montant <= 0:
                return False, "Le montant doit être supérieur à zéro."
            if montant > reste:
                return False, f"Le montant dépasse le reste à payer ({int(reste):,} FCFA).".replace(",", " ")
            date_versement = date_versement or date.today()
            if date_versement > date.today():
                return False, "La date du versement ne peut pas être dans le futur."
            numero = f"INT-{datetime.now():%Y%m%d%H%M%S%f}"
            versement = VersementInternat(
                IDInscriptionInternat=id_internat, NumeroRecu=numero,
                DateVersement=date_versement, Montant=montant,
                ModePaiement=mode.strip().upper() or "ESPECES",
                ReferencePaiement=reference.strip() or None,
                Login=AppSession.get_logged_in_username(),
            )
            session.add(versement)
            session.flush()
            complet = all(p.QuantiteRecue >= p.QuantiteDemandee for p in row.pieces if p.Obligatoire)
            if complet:
                row.Statut = "ADMISE"
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
            rows = session.query(VersementInternat, InscriptionInternat, Eleve).join(
                InscriptionInternat, VersementInternat.IDInscriptionInternat == InscriptionInternat.IDInscriptionInternat
            ).join(Eleve, InscriptionInternat.IDEleve == Eleve.IDEleve).filter(
                InscriptionInternat.IDTAnneeScolaire == id_annee
            ).order_by(VersementInternat.DateVersement.desc(), VersementInternat.IDVersementInternat.desc()).all()
            return [{"id": v.IDVersementInternat, "recu": v.NumeroRecu, "date": v.DateVersement, "nom": f"{e.Nom} {e.Prenoms}", "montant": float(v.Montant), "mode": v.ModePaiement, "annule": v.Annule} for v, _, e in rows]
        finally:
            session.close()

    @staticmethod
    def annuler_versement(id_versement: int, motif: str) -> tuple[bool, str]:
        denied = permission_denied("INTERNAT_VERSEMENTS", "annuler un versement d'internat")
        if denied:
            return denied
        if not motif or not motif.strip():
            return False, "Le motif d'annulation est obligatoire."
        session = get_session()
        try:
            versement = session.get(VersementInternat, id_versement)
            if not versement:
                return False, "Versement introuvable."
            if versement.Annule:
                return False, "Ce versement est déjà annulé."
            versement.annuler(motif.strip(), AppSession.get_logged_in_username())
            session.flush()

            # Reevalue le statut comme le fait verser() : sans cela, annuler le
            # dernier versement d'une pensionnaire ADMISE la laissait ADMISE
            # avec un solde restant a payer identique au montant total (bug
            # constate en test QA). On ne touche pas aux statuts terminaux/
            # manuels SUSPENDUE et SORTIE.
            row = session.get(InscriptionInternat, versement.IDInscriptionInternat)
            if row and row.Statut not in ("SUSPENDUE", "SORTIE"):
                complet = all(p.QuantiteRecue >= p.QuantiteDemandee for p in row.pieces if p.Obligatoire)
                total_verse = session.query(func.coalesce(func.sum(VersementInternat.Montant), 0)).filter_by(
                    IDInscriptionInternat=row.IDInscriptionInternat, Annule=False
                ).scalar()
                row.Statut = "ADMISE" if complet and total_verse > 0 else ("EN_ATTENTE_PAIEMENT" if complet else "DOSSIER_INCOMPLET")

            session.commit()
            return True, "Versement annulé avec traçabilité."
        except Exception as exc:
            session.rollback()
            return False, f"Erreur : {exc}"
        finally:
            session.close()

    @staticmethod
    def dashboard(id_annee: int) -> dict:
        rows = InternatService.get_pensionnaires(id_annee)
        return {
            "effectif": len(rows),
            "admises": sum(r["statut"] == "ADMISE" for r in rows),
            "dossiers_incomplets": sum(r["statut"] == "DOSSIER_INCOMPLET" for r in rows),
            "attendu": sum(r["montant"] for r in rows),
            "encaisse": sum(r["verse"] for r in rows),
            "reste": sum(r["reste"] for r in rows),
        }
