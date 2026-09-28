from datetime import date

from models.eleve import Eleve
from services.famille_service import FamilleService
from tests.factories import make_famille


def test_saisie_pere_cree_et_associe_automatiquement_la_famille(db_session):
    eleve = Eleve(Matricule="26-C01", Nom="Test", Prenoms="Un", DateNaissance=date(2015, 1, 1), Sexe=1)
    db_session.add(eleve)
    db_session.commit()

    ok, message, id_famille = FamilleService.enregistrer_contacts_eleve(eleve.IDEleve, {
        "Principal": "PERE",
        "NomPere": "KOUASSI JEAN",
        "TelPere": "0700000000",
        "TelBureauPere": "0100000000",
        "EmailPere": "pere@example.com",
    })

    assert ok, message
    db_session.expire_all()
    eleve_relu = db_session.get(Eleve, eleve.IDEleve)
    assert eleve_relu.IDFamille == id_famille
    assert eleve_relu.famille.NomPere == "KOUASSI JEAN"
    assert eleve_relu.famille.NomResponsable == "KOUASSI JEAN"
    assert eleve_relu.famille.EmailPere == "pere@example.com"


def test_contact_principal_exige_nom_et_telephone(db_session):
    eleve = Eleve(Matricule="26-C02", Nom="Test", Prenoms="Deux", DateNaissance=date(2015, 1, 1), Sexe=1)
    db_session.add(eleve)
    db_session.commit()

    ok, message, id_famille = FamilleService.enregistrer_contacts_eleve(eleve.IDEleve, {
        "Principal": "MERE", "NomMere": "KOFFI MARIE", "TelMere": "",
    })

    assert not ok
    assert id_famille is None
    assert "nom et un téléphone" in message


def test_meme_contact_principal_regroupe_deux_enfants(db_session):
    famille = make_famille(db_session, nom="YAO PAUL", tel="0500000000")
    eleve = Eleve(Matricule="26-C03", Nom="Test", Prenoms="Trois", DateNaissance=date(2015, 1, 1), Sexe=1)
    db_session.add(eleve)
    db_session.commit()

    ok, message, id_famille = FamilleService.enregistrer_contacts_eleve(eleve.IDEleve, {
        "Principal": "TUTEUR",
        "NomTuteur": "YAO PAUL",
        "CelTuteur": "0500000000",
    })

    assert ok, message
    assert id_famille == famille.IdTFamille
