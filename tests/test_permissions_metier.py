from app.session import AppSession
from models.classe import TClasse
from models.etablissement import EtablissementEcole
from models.prestation_annexe import PrestationAnnexe
from services.classe_service import ClasseService
from services.prestation_service import PrestationService
from tests.factories import make_annee, make_niveau_classe


def _set_user_without_param_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 999,
            "Login": "lecture",
            "Nom": "Lecture",
            "Prenoms": "Seule",
            "ProfilCode": "LECTURE",
            "ProfilLibelle": "Lecture seule",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_VIEW"},
    )


def _set_user_with_param_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1000,
            "Login": "param_admin",
            "Nom": "Param",
            "Prenoms": "Admin",
            "ProfilCode": "PARAM",
            "ProfilLibelle": "Parametres",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_VIEW", "PARAMETRES_MODIFIER"},
    )


def _set_user_without_prestation_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1001,
            "Login": "prest_lecture",
            "Nom": "Prest",
            "Prenoms": "Lecture",
            "ProfilCode": "PREST_READ",
            "ProfilLibelle": "Prestations lecture",
            "IsAdmin": False,
        },
        permissions={"PRESTATIONS_VIEW"},
    )


def _set_user_with_prestation_write_permission():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 1002,
            "Login": "prest_admin",
            "Nom": "Prest",
            "Prenoms": "Admin",
            "ProfilCode": "PREST_WRITE",
            "ProfilLibelle": "Prestations ecriture",
            "IsAdmin": False,
        },
        permissions={"PRESTATIONS_VIEW", "PRESTATIONS_MODIFIER"},
    )


def _setup_active_param_context(db_session):
    annee = make_annee(db_session)
    etablissement = EtablissementEcole(RaisonSociale="Ecole test")
    db_session.add(etablissement)
    db_session.commit()
    niveau, classe = make_niveau_classe(db_session, annee)

    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    AppSession._active_etab_id = etablissement.IDEtablissement_Ecole
    return annee, etablissement, niveau, classe


def test_parametres_write_service_requires_modifier_permission(db_session):
    annee, etablissement, niveau, classe = _setup_active_param_context(db_session)
    _set_user_without_param_write_permission()

    ok, msg = ClasseService.add_classe(
        lib_classe="CM2 NON AUTORISEE",
        sigle="CM2NA",
        id_cycle=niveau.IDT_Cycle,
        id_niveau=niveau.IDT_Niveau,
        capacite=40,
    )

    db_session.expire_all()
    assert ok is False
    assert "PARAMETRES_MODIFIER" in msg
    assert (
        db_session.query(TClasse)
        .filter_by(LibClasse="CM2 NON AUTORISEE")
        .first()
        is None
    )


def test_parametres_write_service_allows_modifier_permission(db_session):
    annee, etablissement, niveau, classe = _setup_active_param_context(db_session)
    _set_user_with_param_write_permission()

    ok, msg = ClasseService.add_classe(
        lib_classe="CM2 AUTORISEE",
        sigle="CM2A",
        id_cycle=niveau.IDT_Cycle,
        id_niveau=niveau.IDT_Niveau,
        capacite=40,
    )

    db_session.expire_all()
    assert ok is True, msg
    assert (
        db_session.query(TClasse)
        .filter_by(LibClasse="CM2 AUTORISEE")
        .first()
        is not None
    )


def test_prestations_write_service_requires_modifier_permission(db_session):
    _set_user_without_prestation_write_permission()

    ok, msg = PrestationService.create_prestation({
        "Code": "MUSIQUE_TEST",
        "Libelle": "Musique test",
        "MontantAnnuel": 8000,
    })

    db_session.expire_all()
    assert ok is False
    assert "PRESTATIONS_MODIFIER" in msg
    assert db_session.query(PrestationAnnexe).filter_by(Code="MUSIQUE_TEST").first() is None


def test_prestations_write_service_allows_modifier_permission(db_session):
    _set_user_with_prestation_write_permission()

    ok, msg = PrestationService.create_prestation({
        "Code": "MUSIQUE_TEST",
        "Libelle": "Musique test",
        "MontantAnnuel": 8000,
    })

    db_session.expire_all()
    assert ok is True, msg
    assert db_session.query(PrestationAnnexe).filter_by(Code="MUSIQUE_TEST").first() is not None
