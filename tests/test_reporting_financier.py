from datetime import date
from decimal import Decimal

from app.session import AppSession
from models.compte import Compte
from models.sortie_fin import SortieFin
from models.versement_scol import VersementScol
from services.dashboard_service import DashboardService
from services.statistiques_service import StatistiquesService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_montant_cantine,
    make_montant_scol,
    make_montant_transport,
    make_niveau_classe,
)


def _setup_reporting(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="REPORT1")
    make_inscription(
        db_session,
        annee,
        famille,
        eleve,
        niveau,
        classe,
        cantine=True,
        transport=True,
    )
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)
    return annee, niveau, famille, eleve


def _add_versement(
    db_session,
    annee,
    famille,
    eleve,
    *,
    scol=0,
    cantine=0,
    transport=0,
    autres=0,
    reduction=False,
    annule=False,
):
    versement = VersementScol(
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        IDFamille=famille.IdTFamille,
        IDEleve=eleve.IDEleve,
        DateVers=date.today(),
        MontantVersSco=scol,
        MontantCantine=cantine,
        MontantVersTrans=transport,
        MontantVersAutres=autres,
        Reduction=reduction,
        Annule=annule,
    )
    db_session.add(versement)
    db_session.commit()
    return versement


def _add_depense(db_session, annee, montant, *, annule=False):
    compte = db_session.query(Compte).filter_by(NumCompte="601").first()
    if compte is None:
        compte = Compte(NumCompte="601", LibCompte="Achats")
        db_session.add(compte)
        db_session.commit()
    db_session.add(
        SortieFin(
            Benef="Fournisseur",
            Montant=montant,
            DateSortie=date.today(),
            IDAnSco=annee.IDTAnneeScolaire,
            DebitCredit="Debit",
            IDCompte=compte.IDCompte,
            Annule=annule,
        )
    )
    db_session.commit()


def test_dashboard_totals_exclude_cancelled_payments(db_session):
    annee, _, famille, eleve = _setup_reporting(db_session)
    _add_versement(db_session, annee, famille, eleve, scol=10_000)
    _add_versement(db_session, annee, famille, eleve, scol=90_000, annule=True)

    summary = DashboardService.get_dashboard_summary()

    assert summary["total_versements_scolarite"] == Decimal("10000.00")
    assert summary["total_recettes"] == Decimal("10000.00")


def test_dashboard_total_depenses_excludes_cancelled_sortie_fin(db_session):
    annee, _, _, _ = _setup_reporting(db_session)
    _add_depense(db_session, annee, 7_000)
    _add_depense(db_session, annee, 11_000, annule=True)

    summary = DashboardService.get_dashboard_summary()

    assert summary["total_depenses"] == Decimal("7000.00")


def test_dashboard_total_recettes_includes_other_fees(db_session):
    annee, _, famille, eleve = _setup_reporting(db_session)
    _add_versement(db_session, annee, famille, eleve, autres=4_000)

    summary = DashboardService.get_dashboard_summary()

    assert summary["total_recettes"] == Decimal("4000.00")


def test_impayes_ignore_cancelled_payments_and_reductions(db_session):
    annee, niveau, famille, eleve = _setup_reporting(db_session)
    make_montant_scol(db_session, annee, niveau, montant_affecte=100_000)
    _add_versement(db_session, annee, famille, eleve, scol=20_000)
    _add_versement(db_session, annee, famille, eleve, scol=50_000, reduction=True)
    _add_versement(db_session, annee, famille, eleve, scol=25_000, annule=True)

    impayes = DashboardService.get_impayes_scolarite()

    assert impayes == [{
        "eleve": "Kouassi Jean",
        "classe": "CM2 A",
        "du": "100 000 F",
        "verse": "20 000 F",
        "reste": "80 000 F",
    }]


def test_statistics_ignore_cancelled_payments_in_all_payment_reports(db_session):
    annee, niveau, famille, eleve = _setup_reporting(db_session)
    make_montant_scol(db_session, annee, niveau, montant_affecte=100_000)
    make_montant_cantine(db_session, annee, niveau, montant=20_000)
    make_montant_transport(db_session, annee, niveau, montant=15_000)
    _add_versement(db_session, annee, famille, eleve, scol=10_000, cantine=2_000, transport=3_000)
    _add_versement(db_session, annee, famille, eleve, scol=60_000, cantine=9_000, transport=8_000, annule=True)
    _add_versement(db_session, annee, famille, eleve, scol=5_000, reduction=True)
    _add_versement(db_session, annee, famille, eleve, scol=7_000, reduction=True, annule=True)

    scolarite = StatistiquesService.get_etat_versements_scolarite()[0]
    cantine = StatistiquesService.get_etat_versements_cantine()[0]
    transport = StatistiquesService.get_etat_versements_transport()[0]

    assert scolarite["MontantVerse"] == 10_000
    assert scolarite["Reduction"] == 5_000
    assert scolarite["Reste"] == 85_000
    assert cantine["MontantVerse"] == 2_000
    assert cantine["Reste"] == 18_000
    assert transport["MontantVerse"] == 3_000
    assert transport["Reste"] == 12_000
