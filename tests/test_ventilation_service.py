from datetime import date

from services.ventilation_service import VentilationService
from services.versement_service import VersementService
from tests.factories import (
    make_annee, make_niveau_classe, make_famille, make_eleve,
    make_inscription, make_montant_scol, make_prestation,
)


def _setup_eleve(db_session, scol_due=100000, scolarite=True):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session, ens_cat_primaire=False)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    if scolarite:
        make_montant_scol(db_session, annee, niveau, montant=scol_due, montant_pri=scol_due, montant_sec=scol_due)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, scolarite=scolarite)
    return annee, eleve, famille


def test_no_payment_gives_zero_ventilation(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000)
    make_prestation(db_session, "MUSIQUE", 50000)

    result = VentilationService.recalculate_student_ventilation(eleve.IDEleve, annee.IDTAnneeScolaire)

    assert result["success"] is True
    assert all(p["montant_ventile"] == 0.0 for p in result["prestations"])


def test_partial_payment_covers_in_creation_order(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000)
    make_prestation(db_session, "MUSIQUE", 50000)

    VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=40000, m_trans=0, m_cant=0, m_autres=0,
    )

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    par_code = {v["code"]: v for v in ventilations}

    assert par_code["ANGLAIS"]["montant_ventile"] == 30000.0  # couverte integralement en premier
    assert par_code["MUSIQUE"]["montant_ventile"] == 10000.0  # recoit le reliquat


def test_full_payment_covers_all_prestations(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000)
    make_prestation(db_session, "MUSIQUE", 50000)

    VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=80000, m_trans=0, m_cant=0, m_autres=0,
    )

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    par_code = {v["code"]: v for v in ventilations}

    assert par_code["ANGLAIS"]["montant_ventile"] == 30000.0
    assert par_code["ANGLAIS"]["taux"] == 1.0
    assert par_code["MUSIQUE"]["montant_ventile"] == 50000.0
    assert par_code["MUSIQUE"]["taux"] == 1.0


def test_surplus_beyond_last_prestation_is_ignored(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000)
    make_prestation(db_session, "MUSIQUE", 50000)

    # Paye la totalite du du (100000), alors que les prestations ne totalisent que 80000.
    VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=100000, m_trans=0, m_cant=0, m_autres=0,
    )

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    total_ventile = sum(v["montant_ventile"] for v in ventilations)

    assert total_ventile == 80000.0  # les 20000 restants ne sont ventiles nulle part


def test_scolarite_non_due_resets_ventilations(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000)
    VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=30000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)

    # Recalcul avec un du a zero (ex: prestation reconfiguree, montant scol supprime)
    result = VentilationService.recalculate_student_ventilation(eleve.IDEleve, 999999)
    assert result["success"] is True
    assert result["prestations"] == []
    assert "warning" in result


def test_inactive_prestation_is_ignored(db_session):
    annee, eleve, famille = _setup_eleve(db_session, scol_due=100000)
    make_prestation(db_session, "ANGLAIS", 30000, is_active=True)
    make_prestation(db_session, "ARCHIVEE", 20000, is_active=False)

    VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=50000, m_trans=0, m_cant=0, m_autres=0,
    )

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    codes = {v["code"] for v in ventilations}

    assert "ARCHIVEE" not in codes
    assert "ANGLAIS" in codes
