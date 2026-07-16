from services.classe_service import ClasseService
from tests.factories import make_annee, make_niveau_classe, make_famille, make_eleve, make_inscription


def test_delete_classe_blocked_when_inscription_exists(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="M001")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    ok, msg = ClasseService.delete_classe(classe.IDTClasse)

    assert ok is False
    assert "inscription" in msg.lower()


def test_delete_classe_succeeds_without_inscription(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)

    ok, msg = ClasseService.delete_classe(classe.IDTClasse)

    assert ok is True
