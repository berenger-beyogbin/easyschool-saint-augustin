from services.niveau_service import NiveauService
from tests.factories import make_annee, make_niveau_classe, make_famille, make_eleve, make_inscription


def test_delete_niveau_blocked_when_classe_exists(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)

    ok, msg = NiveauService.delete_niveau(niveau.IDT_Niveau)

    assert ok is False
    assert "classe" in msg.lower()


def test_delete_niveau_blocked_when_inscription_references_it_directly(db_session):
    """L'inscription peut referencer un niveau directement (TInscription.IDNiveau),
    independamment de la classe choisie : la garde doit couvrir ce cas aussi,
    pas seulement la presence de classes rattachees au niveau."""
    annee = make_annee(db_session)
    niveau_cible, _classe_non_utilisee = make_niveau_classe(db_session, annee, libelle_niveau="6eme")
    _autre_niveau, autre_classe = make_niveau_classe(db_session, annee, libelle_niveau="5eme")

    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="M002")
    make_inscription(db_session, annee, famille, eleve, niveau_cible, autre_classe)

    # Supprimer la classe du niveau cible (aucune inscription ne la reference)
    from models.classe import TClasse
    db_session.query(TClasse).filter_by(IDTClasse=_classe_non_utilisee.IDTClasse).delete()
    db_session.commit()

    ok, msg = NiveauService.delete_niveau(niveau_cible.IDT_Niveau)

    assert ok is False
    assert "inscription" in msg.lower()


def test_delete_niveau_succeeds_without_classe_or_inscription(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    from models.classe import TClasse
    db_session.query(TClasse).filter_by(IDTClasse=classe.IDTClasse).delete()
    db_session.commit()

    ok, msg = NiveauService.delete_niveau(niveau.IDT_Niveau)

    assert ok is True
