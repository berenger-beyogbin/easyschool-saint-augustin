from datetime import date

from services.eleve_service import EleveService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_niveau_classe,
)


def test_search_eleves_par_matricule(db_session):
    famille = make_famille(db_session)
    make_eleve(db_session, famille, matricule="26-001", nom="Koffi", prenoms="Marie")

    resultats = EleveService.search_eleves("26-001")

    assert len(resultats) == 1
    assert resultats[0]["matricule"] == "26-001"
    assert resultats[0]["nom"] == "Koffi"


def test_search_eleves_par_nom_prenom(db_session):
    famille = make_famille(db_session)
    make_eleve(db_session, famille, matricule="26-002", nom="Yao", prenoms="Paul")
    make_eleve(db_session, famille, matricule="26-003", nom="Kouassi", prenoms="Alice")

    resultats_nom = EleveService.search_eleves("Yao")
    resultats_prenom = EleveService.search_eleves("Alice")

    assert [r["matricule"] for r in resultats_nom] == ["26-002"]
    assert [r["matricule"] for r in resultats_prenom] == ["26-003"]


def test_get_eleve_by_id_avec_famille(db_session):
    famille = make_famille(db_session, nom="Kouassi")
    eleve = make_eleve(db_session, famille, matricule="26-004")

    # La session db_session est fermee comme toute session applicative : on
    # relit via le service pour verifier qu'aucune relation lazy n'echoue
    # apres fermeture (DetachedInstanceError) — famille doit deja etre chargee.
    fiche = EleveService.get_eleve_by_id(eleve.IDEleve)

    assert fiche is not None
    assert fiche.famille is not None
    assert fiche.famille.NomResponsable == "Kouassi"


def test_eleve_sans_famille_visible_dans_recherche(db_session):
    from models.eleve import Eleve
    from datetime import date

    orphelin = Eleve(
        Matricule="26-005", Nom="SansFamille", Prenoms="Test",
        DateNaissance=date(2015, 1, 1), Sexe=1, IDFamille=None,
    )
    db_session.add(orphelin)
    db_session.commit()

    resultats = EleveService.search_eleves("SansFamille")

    assert len(resultats) == 1
    assert resultats[0]["id_famille"] is None
    assert resultats[0]["famille_label"] == ""


def test_search_eleves_statut_inscrit_et_classe_actuelle(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    inscrit = make_eleve(db_session, famille, matricule="26-006", nom="Inscrite")
    make_eleve(db_session, famille, matricule="26-007", nom="NonInscrite")
    make_inscription(db_session, annee, famille, inscrit, niveau, classe)

    resultats = {
        r["matricule"]: r
        for r in EleveService.search_eleves("", id_annee=annee.IDTAnneeScolaire)
    }

    assert resultats["26-006"]["inscrit"] is True
    assert resultats["26-006"]["classe_libelle"] == classe.LibClasse
    assert resultats["26-007"]["inscrit"] is False
    assert resultats["26-007"]["classe_libelle"] == ""


def test_associer_famille(db_session):
    famille = make_famille(db_session)
    from models.eleve import Eleve
    from datetime import date
    eleve = Eleve(
        Matricule="26-008", Nom="AAssocier", Prenoms="Test",
        DateNaissance=date(2015, 1, 1), Sexe=2, IDFamille=None,
    )
    db_session.add(eleve)
    db_session.commit()

    ok, message = EleveService.associer_famille(eleve.IDEleve, famille.IdTFamille)

    assert ok, message
    fiche = EleveService.get_eleve_by_id(eleve.IDEleve)
    assert fiche.IDFamille == famille.IdTFamille


def test_absence_de_suppression_en_cascade_accidentelle(db_session):
    """Un élève avec une inscription ne doit jamais pouvoir être supprimé
    (protection déjà existante, vérifiée pour ne pas régresser)."""
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="26-009")
    make_inscription(db_session, annee, famille, eleve, niveau, classe)

    ok, message = EleveService.delete_eleve(eleve.IDEleve)

    assert not ok
    assert "inscription" in message.lower()
    from models.eleve import Eleve
    assert db_session.get(Eleve, eleve.IDEleve) is not None


def _minimal_eleve_data(matricule, matricule_national):
    return {
        "Matricule": matricule,
        "MatriculeNational": matricule_national,
        "Nom": "KOFFI",
        "Prenoms": "Jean",
        "DateNaissance": date(2014, 1, 1),
        "Sexe": 1,
    }


def test_create_eleve_normalise_matricule_national(db_session):
    ok, message = EleveService.create_eleve(_minimal_eleve_data("26-010", "  ci 26440774j "))

    assert ok, message
    from models.eleve import Eleve
    eleve = db_session.query(Eleve).filter_by(Matricule="26-010").one()
    assert eleve.MatriculeNational == "CI26440774J"


def test_create_eleve_refuse_matricule_national_existant_normalise(db_session):
    ok, message = EleveService.create_eleve(_minimal_eleve_data("26-011", "2644 0774j"))
    assert ok, message

    ok, message = EleveService.create_eleve(_minimal_eleve_data("26-012", " 26440774J "))

    assert not ok
    assert "26-011" in message
    assert "appartient" in message


def test_update_eleve_accepte_son_propre_matricule_national(db_session):
    ok, message = EleveService.create_eleve(_minimal_eleve_data("26-013", "24271331d"))
    assert ok, message
    from models.eleve import Eleve
    eleve = db_session.query(Eleve).filter_by(Matricule="26-013").one()

    data = _minimal_eleve_data("26-013", " 2427 1331D ")
    data["Prenoms"] = "Jean Paul"
    ok, message = EleveService.update_eleve(eleve.IDEleve, data)

    assert ok, message
    db_session.expire_all()
    assert db_session.get(Eleve, eleve.IDEleve).MatriculeNational == "24271331D"
