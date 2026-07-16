from datetime import date

from app.session import AppSession
from models.compte import Compte
from models.sortie_fin import SortieFin
from models.type_sortie import TypeSortie
from services.comptabilite_service import ComptabiliteService
from services.compte_service import CompteService
from services.type_sortie_service import TypeSortieService
from tests.factories import make_annee


def _set_user(permissions: set[str]):
    AppSession.set_current_user(
        {
            "IDUtilisateur": 2000,
            "Login": "compta_test",
            "Nom": "Compta",
            "Prenoms": "Test",
            "ProfilCode": "COMPTA",
            "ProfilLibelle": "Comptabilite",
            "IsAdmin": False,
        },
        permissions=permissions,
    )


def _setup_compta_context(db_session):
    annee = make_annee(db_session)
    compte = Compte(NumCompte="6250", LibCompte="Deplacements")
    db_session.add(compte)
    db_session.commit()
    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    return annee, compte


def test_create_mouvement_requires_comptabilite_saisie_permission(db_session):
    annee, compte = _setup_compta_context(db_session)
    _set_user({"COMPTABILITE_VIEW"})

    ok, msg = ComptabiliteService.create_mouvement(
        benef="Fournisseur",
        montant=15000,
        date_sortie=date.today(),
        id_compte=compte.IDCompte,
        debit_credit="Debit",
    )

    db_session.expire_all()
    assert ok is False
    assert "COMPTABILITE_SAISIE" in msg
    assert db_session.query(SortieFin).count() == 0


def test_create_compte_requires_comptabilite_saisie_permission(db_session):
    _set_user({"COMPTABILITE_VIEW"})

    ok, msg = CompteService.create_compte("6060", "Achats interdits")

    db_session.expire_all()
    assert ok is False
    assert "COMPTABILITE_SAISIE" in msg
    assert db_session.query(Compte).filter_by(NumCompte="6060").first() is None


def test_create_type_sortie_requires_comptabilite_saisie_permission(db_session):
    annee, compte = _setup_compta_context(db_session)
    _set_user({"COMPTABILITE_VIEW"})

    ok, msg = TypeSortieService.create_type_sortie(
        "Fournitures interdites",
        compte.IDCompte,
        "Debit",
    )

    db_session.expire_all()
    assert ok is False
    assert "COMPTABILITE_SAISIE" in msg
    assert db_session.query(TypeSortie).count() == 0


def test_create_mouvement_allowed_with_comptabilite_saisie_permission(db_session):
    annee, compte = _setup_compta_context(db_session)
    _set_user({"COMPTABILITE_VIEW", "COMPTABILITE_SAISIE"})

    ok, msg = ComptabiliteService.create_mouvement(
        benef="Fournisseur",
        montant=15000,
        date_sortie=date.today(),
        id_compte=compte.IDCompte,
        debit_credit="Debit",
    )

    db_session.expire_all()
    assert ok is True, msg
    mouvement = db_session.query(SortieFin).first()
    assert mouvement is not None
    assert mouvement.IDAnSco == annee.IDTAnneeScolaire


def test_update_mouvement_requires_comptabilite_saisie_permission(db_session):
    annee, compte = _setup_compta_context(db_session)
    mouvement = SortieFin(
        Benef="Fournisseur",
        Montant=15000,
        DateSortie=date.today(),
        CodeSortie="SF-2026-0001",
        IDAnSco=annee.IDTAnneeScolaire,
        DebitCredit="Debit",
        IDCompte=compte.IDCompte,
    )
    db_session.add(mouvement)
    db_session.commit()
    _set_user({"COMPTABILITE_VIEW"})

    ok, msg = ComptabiliteService.update_mouvement(
        mouvement.IDSortieFin,
        benef="Fournisseur modifie",
        montant=20000,
        date_sortie=date.today(),
        id_compte=compte.IDCompte,
        debit_credit="Debit",
    )

    db_session.expire_all()
    assert ok is False
    assert "COMPTABILITE_SAISIE" in msg
    assert db_session.get(SortieFin, mouvement.IDSortieFin).Montant == 15000


def test_update_mouvement_rejects_unknown_account(db_session):
    annee, compte = _setup_compta_context(db_session)
    mouvement = SortieFin(
        Benef="Fournisseur",
        Montant=15000,
        DateSortie=date.today(),
        CodeSortie="SF-2026-0001",
        IDAnSco=annee.IDTAnneeScolaire,
        DebitCredit="Debit",
        IDCompte=compte.IDCompte,
    )
    db_session.add(mouvement)
    db_session.commit()
    _set_user({"COMPTABILITE_VIEW", "COMPTABILITE_SAISIE"})

    ok, msg = ComptabiliteService.update_mouvement(
        mouvement.IDSortieFin,
        benef="Fournisseur modifie",
        montant=20000,
        date_sortie=date.today(),
        id_compte=999999,
        debit_credit="Debit",
    )

    assert ok is False
    assert "compte" in msg.lower()


def test_delete_mouvement_requires_comptabilite_saisie_permission(db_session):
    annee, compte = _setup_compta_context(db_session)
    mouvement = SortieFin(
        Benef="Fournisseur",
        Montant=15000,
        DateSortie=date.today(),
        CodeSortie="SF-2026-0001",
        IDAnSco=annee.IDTAnneeScolaire,
        DebitCredit="Debit",
        IDCompte=compte.IDCompte,
    )
    db_session.add(mouvement)
    db_session.commit()
    _set_user({"COMPTABILITE_VIEW"})

    ok, msg = ComptabiliteService.delete_mouvement(mouvement.IDSortieFin)

    db_session.expire_all()
    assert ok is False
    assert "COMPTABILITE_SAISIE" in msg
    assert db_session.get(SortieFin, mouvement.IDSortieFin) is not None
