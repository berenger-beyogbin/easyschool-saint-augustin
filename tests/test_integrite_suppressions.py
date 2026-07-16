import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.session import AppSession
from models.classe import TClasse
from models.inscription import TInscription
from models.versement_scol import VersementScol
from services.classe_service import ClasseService
from services.eleve_service import EleveService
from services.versement_service import VersementService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_montant_scol,
    make_niveau_classe,
)


def _setup_inscription(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-SAFE-001")
    make_montant_scol(db_session, annee, niveau)
    inscription = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    return annee, niveau, classe, famille, eleve, inscription


def _setup_versement(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    ok, msg, versement_id = VersementService.create_versement(
        annee.IDTAnneeScolaire,
        eleve.IDEleve,
        famille.IdTFamille,
        inscription.DateInscription,
        m_scol=10_000,
        m_trans=0,
        m_cant=0,
        m_autres=0,
        login="TEST",
    )
    assert ok is True, msg
    return annee, niveau, classe, famille, eleve, inscription, versement_id


def _set_param_modifier_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 2000,
            "Login": "param_admin",
            "Nom": "Param",
            "ProfilCode": "PARAM",
            "ProfilLibelle": "Parametres",
            "IsAdmin": False,
        },
        permissions={"PARAMETRES_MODIFIER"},
    )


def test_delete_classe_with_inscriptions_is_refused_and_preserves_history(db_session):
    """Une classe contenant des inscriptions ne doit jamais être supprimée en cascade."""
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    _set_param_modifier_user()

    ok, msg = ClasseService.delete_classe(classe.IDTClasse)

    db_session.expire_all()
    assert ok is False
    assert "inscription" in msg.lower() or "utilis" in msg.lower()
    assert db_session.get(TClasse, classe.IDTClasse) is not None
    assert (
        db_session.query(TInscription)
        .filter_by(IDTInscription=inscription.IDTInscription)
        .first()
        is not None
    )


def test_eleve_service_refuses_delete_when_history_exists(db_session):
    """Le service élève protège déjà l'historique : on le verrouille par test."""
    annee, niveau, classe, famille, eleve, inscription, versement_id = _setup_versement(db_session)

    ok, msg = EleveService.delete_eleve(eleve.IDEleve)

    db_session.expire_all()
    assert ok is False
    assert "inscription" in msg.lower() or "versement" in msg.lower()
    assert db_session.get(VersementScol, versement_id) is not None


def test_database_rejects_direct_delete_of_classe_with_inscriptions(db_session):
    """Même hors service applicatif, la base doit refuser d'effacer une classe historisée."""
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text('DELETE FROM "TClasse" WHERE "IDTClasse" = :id_classe'),
            {"id_classe": classe.IDTClasse},
        )
        db_session.commit()


def test_database_rejects_direct_delete_of_eleve_with_financial_history(db_session):
    """La base doit protéger élèves, inscriptions et versements contre les suppressions directes."""
    annee, niveau, classe, famille, eleve, inscription, versement_id = _setup_versement(db_session)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text('DELETE FROM "Eleve" WHERE "IDEleve" = :id_eleve'),
            {"id_eleve": eleve.IDEleve},
        )
        db_session.commit()


def test_database_rejects_direct_delete_of_annee_with_financial_history(db_session):
    """Une année contenant inscriptions/versements doit être archivée ou clôturée, pas supprimée."""
    annee, niveau, classe, famille, eleve, inscription, versement_id = _setup_versement(db_session)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text('DELETE FROM "TAnneeScolaire" WHERE "IDTAnneeScolaire" = :id_annee'),
            {"id_annee": annee.IDTAnneeScolaire},
        )
        db_session.commit()
