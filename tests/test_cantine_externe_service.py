from datetime import date

from models.cantine_externe import InscriptionCantine, VersementCantine
from models.eleve import Eleve
from services.cantine_externe_service import CantineExterneService
from tests.factories import make_annee


def _inscrire(db_session):
    annee = make_annee(db_session)
    donnees = {
        "nom": "KONE", "prenoms": "Awa", "date_naissance": date(2014, 6, 1), "sexe": 2,
        "responsable_nom": "Resp", "responsable_contact": "0500000000",
    }
    ok, message = CantineExterneService.inscrire_externe(annee.IDTAnneeScolaire, donnees)
    assert ok, message
    return db_session.query(InscriptionCantine).one()


def test_suppression_pensionnaire_cantine_sans_versement(db_session):
    row = _inscrire(db_session)
    ok, message = CantineExterneService.supprimer_pensionnaire(row.IDInscriptionCantine, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(InscriptionCantine).count() == 0
    assert db_session.query(Eleve).count() == 0


def test_suppression_pensionnaire_cantine_exige_motif_et_versements_annules(db_session):
    row = _inscrire(db_session)
    id_ins = row.IDInscriptionCantine

    ok, message = CantineExterneService.supprimer_pensionnaire(id_ins, " ")
    assert not ok and "motif" in message.lower()

    assert CantineExterneService.verser(id_ins, 10_000)[0]
    ok, message = CantineExterneService.supprimer_pensionnaire(id_ins, "Erreur")
    assert not ok and "versement" in message.lower()
    assert db_session.query(InscriptionCantine).count() == 1

    versement = db_session.query(VersementCantine).one()
    assert CantineExterneService.annuler_versement(versement.IDVersementCantine, "Erreur")[0]
    ok, message = CantineExterneService.supprimer_pensionnaire(id_ins, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(InscriptionCantine).count() == 0
    assert db_session.query(VersementCantine).count() == 0
