import pytest

from app.session import AppSession
from models.classe import TClasse
from models.etablissement import EtablissementEcole
from services.classe_service import ClasseService
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


@pytest.mark.xfail(strict=True, reason="Lot permissions : les services métier ne vérifient pas encore les droits.")
def test_parametres_write_service_requires_modifier_permission(db_session):
    annee = make_annee(db_session)
    etablissement = EtablissementEcole(RaisonSociale="Ecole test")
    db_session.add(etablissement)
    db_session.commit()
    niveau, classe = make_niveau_classe(db_session, annee)

    try:
        AppSession._active_annee_id = annee.IDTAnneeScolaire
        AppSession._active_annee_libelle = annee.Libelle
        AppSession._active_etab_id = etablissement.IDEtablissement_Ecole
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
        assert "permission" in msg.lower() or "droit" in msg.lower()
        assert (
            db_session.query(TClasse)
            .filter_by(LibClasse="CM2 NON AUTORISEE")
            .first()
            is None
        )
    finally:
        AppSession._active_annee_id = None
        AppSession._active_annee_libelle = None
        AppSession._active_etab_id = None
        AppSession.set_current_user({}, set())
