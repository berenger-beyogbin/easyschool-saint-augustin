from datetime import date

from models.compte import Compte
from models.versement_scol import VersementScol
from services.comptabilite_service import ComptabiliteService, _SYSCOA_RUBRIQUE
from services.compte_service import SYSCOA_INCOME_ACCOUNTS
from tests.factories import make_annee, make_famille, make_eleve


def _make_versement(session, annee, famille, eleve, m_scol=0, m_trans=0, m_cant=0, m_autres=0):
    v = VersementScol(
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        IDFamille=famille.IdTFamille,
        IDEleve=eleve.IDEleve,
        DateVers=date.today(),
        MontantVersSco=m_scol,
        MontantVersTrans=m_trans,
        MontantCantine=m_cant,
        MontantVersAutres=m_autres,
    )
    session.add(v)
    session.commit()
    return v


def _seed_comptes_syscoa(session):
    for num, lib in SYSCOA_INCOME_ACCOUNTS.items():
        session.add(Compte(NumCompte=num, LibCompte=lib))
    session.commit()


def test_7045_autres_frais_account_is_seeded():
    assert SYSCOA_INCOME_ACCOUNTS.get("7045") == "AUTRES FRAIS"
    assert _SYSCOA_RUBRIQUE.get("7045") == "autres"


def test_get_totaux_entrees_rubriques_includes_autres(db_session):
    annee = make_annee(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="COMPTA1")
    _make_versement(db_session, annee, famille, eleve, m_scol=10000, m_autres=6000)

    totaux = ComptabiliteService.get_totaux_entrees_rubriques(annee.IDTAnneeScolaire)

    assert totaux["autres"] == 6000.0
    assert totaux["scolarite"] == 10000.0


def test_balance_comptes_credits_autres_frais_exactly_once(db_session):
    """Recette #8 : les autres frais apparaissent exactement une fois dans la balance."""
    annee = make_annee(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="COMPTA2")
    _seed_comptes_syscoa(db_session)
    _make_versement(db_session, annee, famille, eleve, m_autres=6000)

    balance = ComptabiliteService.get_balance_comptes(annee.IDTAnneeScolaire)

    ligne_7045 = next(item for item in balance if item["NumCompte"] == "7045")
    assert ligne_7045["Credit"] == 6000.0
    assert ligne_7045["Solde"] == 6000.0

    # Aucune autre ligne ne doit porter ce montant (pas de double comptage)
    autres_lignes_avec_montant = [
        item for item in balance if item["NumCompte"] != "7045" and item["Credit"] == 6000.0
    ]
    assert autres_lignes_avec_montant == []
