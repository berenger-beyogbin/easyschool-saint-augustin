"""Verifie que ON DELETE RESTRICT bloque reellement la suppression au niveau
base de donnees (audit P0-02), independamment des garde-fous applicatifs des
services (contournables par un acces direct a la base ou un futur bug)."""
import pytest
from sqlalchemy.exc import IntegrityError

from models.classe import TClasse
from models.famille import TFamille
from models.annee_scolaire import TAnneeScolaire
from tests.factories import make_annee, make_niveau_classe, make_famille, make_eleve, make_inscription


def test_delete_classe_blocked_by_db_when_inscription_exists(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="RESTR01")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    db_session.delete(classe)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    assert db_session.get(TClasse, classe.IDTClasse) is not None


def test_delete_famille_blocked_by_db_when_inscription_exists(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="RESTR02")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    with pytest.raises(IntegrityError):
        db_session.delete(famille)
        db_session.commit()
    db_session.rollback()

    assert db_session.get(TFamille, famille.IdTFamille) is not None


def test_delete_annee_blocked_by_db_when_inscription_exists(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="RESTR03")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    with pytest.raises(IntegrityError):
        db_session.delete(annee)
        db_session.commit()
    db_session.rollback()

    assert db_session.get(TAnneeScolaire, annee.IDTAnneeScolaire) is not None
