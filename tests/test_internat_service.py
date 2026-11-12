from datetime import date

from services.internat_service import InternatService
from models.eleve import Eleve
from models.internat import InscriptionInternat, InternatPieceDossier, VersementInternat
from tests.factories import make_annee, make_eleve, make_famille, make_inscription, make_niveau_classe
from services.comptabilite_service import ComptabiliteService
from services.compte_service import SYSCOA_INCOME_ACCOUNTS


def _inscription_fille(db_session, matricule="INT-001"):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule, prenoms="Aminata")
    eleve.Sexe = 2
    db_session.commit()
    inscription = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    return annee, inscription


def test_echeancier_par_defaut_reproduit_la_fiche(db_session):
    annee = make_annee(db_session)
    rows = InternatService.get_echeances(annee.IDTAnneeScolaire)
    assert len(rows) == 4
    assert sum(row.MontantNouvelle for row in rows) == 450_000
    assert sum(row.MontantAncienne for row in rows) == 420_000


def test_inscription_nouvelle_cree_pension_et_dossier(db_session):
    _, inscription = _inscription_fille(db_session)
    ok, _ = InternatService.inscrire(inscription.IDTInscription, "NOUVELLE")
    assert ok
    internat = db_session.query(InscriptionInternat).one()
    assert internat.MontantAnnuel == 450_000
    assert internat.Statut == "DOSSIER_INCOMPLET"
    assert db_session.query(InternatPieceDossier).count() == 6


def test_internat_rejette_un_garcon(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, "INT-GARCON")
    inscription = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    ok, message = InternatService.inscrire(inscription.IDTInscription, "NOUVELLE")
    assert not ok
    assert "réservé aux filles" in message


def test_inscription_pensionnaire_externe_sans_inscription_scolaire(db_session):
    annee = make_annee(db_session)
    donnees = {
        "nom": "KOUAME", "prenoms": "Grâce",
        "date_naissance": date(2015, 4, 12),
        "lieu_naissance": "Attinguié", "habitation": "Village",
        "etablissement": "EPP Attinguié 1", "classe": "CM1",
        "responsable_nom": "Kouamé Jean", "responsable_contact": "0700000000",
    }

    ok, message = InternatService.inscrire_externe(
        annee.IDTAnneeScolaire, donnees, "NOUVELLE"
    )

    assert ok, message
    internat = db_session.query(InscriptionInternat).one()
    eleve = db_session.query(Eleve).one()
    assert internat.IDTInscription is None
    assert internat.IDEleve == eleve.IDEleve
    assert internat.IDTAnneeScolaire == annee.IDTAnneeScolaire
    assert internat.OrigineScolaire == "EXTERNE"
    assert internat.EtablissementFrequente == "EPP Attinguié 1"
    assert eleve.Matricule.startswith("INT-EXT-")
    assert InternatService.get_pensionnaires(annee.IDTAnneeScolaire)[0]["origine"] == "EXTERNE"


def test_paiement_externe_alimente_la_comptabilite(db_session):
    annee = make_annee(db_session)
    donnees = {
        "nom": "YAO", "prenoms": "Awa",
        "date_naissance": date(2014, 6, 1),
        "etablissement": "EPP Attinguié 2", "classe": "CM2",
        "responsable_nom": "Yao Marie", "responsable_contact": "0500000000",
    }
    assert InternatService.inscrire_externe(annee.IDTAnneeScolaire, donnees, "ANCIENNE")[0]
    internat = db_session.query(InscriptionInternat).one()
    assert InternatService.verser(internat.IDInscriptionInternat, 50_000)[0]
    assert ComptabiliteService.get_totaux_entrees_rubriques(annee.IDTAnneeScolaire)["internat"] == 50_000


def test_dossier_complet_attend_paiement_puis_admet(db_session):
    _, inscription = _inscription_fille(db_session)
    assert InternatService.inscrire(inscription.IDTInscription, "ANCIENNE")[0]
    internat = db_session.query(InscriptionInternat).one()
    pieces = InternatService.get_pieces(internat.IDInscriptionInternat)
    quantites = {piece["id"]: piece["demandee"] for piece in pieces}
    assert InternatService.enregistrer_dossier(internat.IDInscriptionInternat, quantites)[0]
    db_session.refresh(internat)
    assert internat.Statut == "EN_ATTENTE_PAIEMENT"
    assert InternatService.verser(internat.IDInscriptionInternat, 50_000)[0]
    db_session.refresh(internat)
    assert internat.Statut == "ADMISE"
    assert db_session.query(VersementInternat).one().Montant == 50_000


def test_versement_ne_peut_depasser_solde(db_session):
    _, inscription = _inscription_fille(db_session)
    assert InternatService.inscrire(inscription.IDTInscription, "NOUVELLE")[0]
    internat = db_session.query(InscriptionInternat).one()
    ok, message = InternatService.verser(internat.IDInscriptionInternat, 450_001)
    assert not ok
    assert "dépasse" in message
    assert db_session.query(VersementInternat).count() == 0


def test_versement_internat_alimente_la_comptabilite(db_session):
    annee, inscription = _inscription_fille(db_session)
    assert SYSCOA_INCOME_ACCOUNTS["7046"] == "PENSION INTERNAT"
    assert InternatService.inscrire(inscription.IDTInscription, "NOUVELLE")[0]
    internat = db_session.query(InscriptionInternat).one()
    assert InternatService.verser(internat.IDInscriptionInternat, 75_000)[0]
    totaux = ComptabiliteService.get_totaux_entrees_rubriques(annee.IDTAnneeScolaire)
    assert totaux["internat"] == 75_000
    versement = db_session.query(VersementInternat).one()
    assert InternatService.annuler_versement(versement.IDVersementInternat, "Erreur de saisie")[0]
    totaux = ComptabiliteService.get_totaux_entrees_rubriques(annee.IDTAnneeScolaire)
    assert totaux["internat"] == 0


def test_annulation_du_dernier_versement_retrograde_le_statut(db_session):
    """annuler_versement() doit reevaluer le statut, pas seulement les totaux.

    Avant correction, annuler l'unique versement d'une pensionnaire ADMISE la
    laissait ADMISE avec un solde restant egal au montant total (verse() ne
    recalcule le statut qu'a la creation d'un versement, jamais a l'annulation).
    """
    _, inscription = _inscription_fille(db_session)
    assert InternatService.inscrire(inscription.IDTInscription, "ANCIENNE")[0]
    internat = db_session.query(InscriptionInternat).one()
    pieces = InternatService.get_pieces(internat.IDInscriptionInternat)
    quantites = {piece["id"]: piece["demandee"] for piece in pieces}
    assert InternatService.enregistrer_dossier(internat.IDInscriptionInternat, quantites)[0]
    assert InternatService.verser(internat.IDInscriptionInternat, 50_000)[0]
    db_session.refresh(internat)
    assert internat.Statut == "ADMISE"

    versement = db_session.query(VersementInternat).one()
    assert InternatService.annuler_versement(versement.IDVersementInternat, "Erreur de saisie")[0]
    db_session.refresh(internat)
    assert internat.Statut == "EN_ATTENTE_PAIEMENT"


def _externe(db_session, nom="KONE"):
    annee = make_annee(db_session)
    donnees = {
        "nom": nom, "prenoms": "Awa", "date_naissance": date(2014, 6, 1),
        "etablissement": "EPP", "classe": "CM2",
        "responsable_nom": "Resp", "responsable_contact": "0500000000",
    }
    assert InternatService.inscrire_externe(annee.IDTAnneeScolaire, donnees, "NOUVELLE")[0]
    return db_session.query(InscriptionInternat).one()


def test_suppression_pensionnaire_externe_supprime_aussi_la_fiche(db_session):
    internat = _externe(db_session)
    ok, message = InternatService.supprimer_pensionnaire(internat.IDInscriptionInternat, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(InscriptionInternat).count() == 0
    assert db_session.query(InternatPieceDossier).count() == 0
    assert db_session.query(Eleve).count() == 0


def test_suppression_pensionnaire_du_college_conserve_leleve(db_session):
    _, inscription = _inscription_fille(db_session)
    assert InternatService.inscrire(inscription.IDTInscription, "NOUVELLE")[0]
    internat = db_session.query(InscriptionInternat).one()
    ok, message = InternatService.supprimer_pensionnaire(internat.IDInscriptionInternat, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(InscriptionInternat).count() == 0
    assert db_session.query(Eleve).count() == 1


def test_suppression_pensionnaire_refusee_avec_versement_ou_sans_motif(db_session):
    internat = _externe(db_session)
    ok, message = InternatService.supprimer_pensionnaire(internat.IDInscriptionInternat, " ")
    assert not ok and "motif" in message.lower()

    assert InternatService.verser(internat.IDInscriptionInternat, 50_000)[0]
    ok, message = InternatService.supprimer_pensionnaire(internat.IDInscriptionInternat, "Erreur")
    assert not ok and "versement" in message.lower()

    versement = db_session.query(VersementInternat).one()
    assert InternatService.annuler_versement(versement.IDVersementInternat, "Erreur")[0]
    ok, message = InternatService.supprimer_pensionnaire(internat.IDInscriptionInternat, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(InscriptionInternat).count() == 0
    assert db_session.query(VersementInternat).count() == 0
