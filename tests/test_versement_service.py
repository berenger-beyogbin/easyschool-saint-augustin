from datetime import date

from app.session import AppSession
from services.versement_service import VersementService
from tests.factories import (
    make_annee, make_niveau_classe, make_famille, make_eleve,
    make_inscription, make_montant_scol, make_montant_transport, make_montant_cantine,
)


def _set_versements_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 3000,
            "Login": "caisse_test",
            "Nom": "Caisse",
            "ProfilCode": "CAISSE",
            "ProfilLibelle": "Caisse",
            "IsAdmin": False,
        },
        permissions={"SCOLARITE_VERSEMENTS"},
    )


def _setup_base(db_session, ens_cat_primaire=True, ebrie_abobote=False, nouveau=False, **ins_opts):
    _set_versements_user()
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session, ebrie_abobote=ebrie_abobote, ens_cat_primaire=ens_cat_primaire)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    make_montant_scol(db_session, annee, niveau, montant=100000, montant_pri=90000, montant_sec=110000)
    ins = make_inscription(db_session, annee, famille, eleve, niveau, classe, nouveau=nouveau, **ins_opts)
    return annee, niveau, classe, famille, eleve, ins


def test_scol_due_uses_primaire_rate_for_primaire_family(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 90000.0


def test_scol_due_uses_default_rate_when_no_category(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(
        db_session, ens_cat_primaire=False,
    )
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 100000.0


def test_ebrie_abobote_reduction_applied(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True, ebrie_abobote=True)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 80000.0  # 90000 - 10000


def test_nouveau_eleve_surcharge_applied(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True, nouveau=True)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 100000.0  # 90000 + 10000


def test_third_child_of_family_gets_reduction(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session, ens_cat_primaire=True)
    make_montant_scol(db_session, annee, niveau, montant=100000, montant_pri=90000, montant_sec=110000)

    eleve1 = make_eleve(db_session, famille, matricule="EL0001", nom="Enfant1")
    eleve2 = make_eleve(db_session, famille, matricule="EL0002", nom="Enfant2")
    eleve3 = make_eleve(db_session, famille, matricule="EL0003", nom="Enfant3")

    make_inscription(db_session, annee, famille, eleve1, niveau, classe)
    make_inscription(db_session, annee, famille, eleve2, niveau, classe)
    make_inscription(db_session, annee, famille, eleve3, niveau, classe)

    fin1 = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve1.IDEleve)
    fin3 = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve3.IDEleve)

    assert fin1["scol_due"] == 90000.0       # 1er enfant : pas de reduction
    assert fin3["scol_due"] == 80000.0       # 3e enfant : -10000


def test_create_versement_rejects_amount_above_reste(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=95000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "depasse" in msg.lower()
    assert new_id is None


def test_create_versement_success_updates_paid_amount(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=50000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is True
    assert new_id is not None

    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_paye"] == 50000.0
    assert fin["scol_reste"] == 40000.0  # 90000 - 50000


def test_create_versement_rejects_negative_amount(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=-100, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "negatifs" in msg.lower()


def test_create_versement_rejects_when_annee_cloturee(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    annee.Cloturer = True
    db_session.commit()

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=10000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "cloturee" in msg.lower()


def test_delete_versement_blocked_when_annee_cloturee(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ens_cat_primaire=True)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=10000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is True

    annee.Cloturer = True
    db_session.commit()

    ok, msg = VersementService.delete_versement(new_id)
    assert ok is False
    assert "cloturee" in msg.lower()
