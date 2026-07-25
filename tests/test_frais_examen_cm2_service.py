from datetime import date

from app.session import AppSession
from services.frais_examen_cm2_service import FraisExamenCM2Service
from tests.factories import (
    make_annee, make_niveau_classe, make_famille, make_eleve, make_inscription,
)


def _set_examen_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 4000,
            "Login": "caisse_test",
            "Nom": "Caisse",
            "ProfilCode": "CAISSE",
            "ProfilLibelle": "Caisse",
            "IsAdmin": False,
        },
        permissions={"EXAMEN_CM2_VIEW"},
    )


def _setup_cm2_eleve(db_session, libelle_niveau="CM2"):
    _set_examen_user()
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau=libelle_niveau)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    ins = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    return annee, niveau, classe, famille, eleve, ins


def test_save_and_get_montant_configure(db_session):
    annee, *_ = _setup_cm2_eleve(db_session)
    success, msg = FraisExamenCM2Service.save_montant(annee.IDTAnneeScolaire, 8000)
    assert success
    assert FraisExamenCM2Service.get_montant_configure(annee.IDTAnneeScolaire) == 8000.0


def test_save_montant_upserts_existing_value(db_session):
    annee, *_ = _setup_cm2_eleve(db_session)
    FraisExamenCM2Service.save_montant(annee.IDTAnneeScolaire, 8000)
    FraisExamenCM2Service.save_montant(annee.IDTAnneeScolaire, 9000)
    assert FraisExamenCM2Service.get_montant_configure(annee.IDTAnneeScolaire) == 9000.0


def test_get_eleves_cm2_lists_only_cm2_level(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_cm2_eleve(db_session, libelle_niveau="CM2")
    autre_niveau, autre_classe = make_niveau_classe(db_session, annee, libelle_niveau="CM1")
    autre_eleve = make_eleve(db_session, famille, matricule="EL0002")
    make_inscription(db_session, annee, famille, autre_eleve, autre_niveau, autre_classe)

    eleves = FraisExamenCM2Service.get_eleves_cm2(annee.IDTAnneeScolaire)
    matricules = [e["matricule"] for e in eleves]
    assert matricules == ["EL0001"]
    assert eleves[0]["paye"] is False


def test_create_versement_marks_eleve_as_paye(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_cm2_eleve(db_session)
    success, msg, new_id = FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire,
        id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille,
        date_v=date.today(),
        montant=8000,
        login="caisse_test",
    )
    assert success
    assert new_id is not None

    eleves = FraisExamenCM2Service.get_eleves_cm2(annee.IDTAnneeScolaire)
    assert eleves[0]["paye"] is True
    assert eleves[0]["montant_paye"] == 8000.0


def test_create_versement_rejects_double_paiement(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_cm2_eleve(db_session)
    FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille, date_v=date.today(), montant=8000,
        login="caisse_test",
    )
    success, msg, new_id = FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille, date_v=date.today(), montant=8000,
        login="caisse_test",
    )
    assert not success
    assert new_id is None


def test_create_versement_blocked_when_annee_cloturee(db_session):
    _set_examen_user()
    annee = make_annee(db_session, cloturer=True)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    success, msg, new_id = FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille, date_v=date.today(), montant=8000,
        login="caisse_test",
    )
    assert not success
    assert "clotur" in msg.lower()


def test_delete_versement_allows_reencaissement(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_cm2_eleve(db_session)
    _, _, new_id = FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille, date_v=date.today(), montant=8000,
        login="caisse_test",
    )
    success, msg = FraisExamenCM2Service.delete_versement(new_id)
    assert success

    eleves = FraisExamenCM2Service.get_eleves_cm2(annee.IDTAnneeScolaire)
    assert eleves[0]["paye"] is False

    success2, msg2, new_id2 = FraisExamenCM2Service.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve,
        id_famille=famille.IdTFamille, date_v=date.today(), montant=8000,
        login="caisse_test",
    )
    assert success2
    assert new_id2 is not None
