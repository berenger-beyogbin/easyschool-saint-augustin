from datetime import date

from app.session import AppSession
from models.versement_scol import VersementScol
from services.statistiques_service import StatistiquesService
from tests.factories import (
    make_annee, make_niveau_classe, make_famille, make_eleve,
    make_inscription, make_montant_scol, make_montant_transport, make_montant_cantine,
)


def _activer_annee(annee):
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)


# ─── Regression : surtaxe "Nouveau" doit suivre la meme regle que VersementService ───

def test_scolarite_surcharge_nouveau_non_appliquee_au_prescolaire(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau="PS")
    famille = make_famille(db_session, ens_cat_primaire=True)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    make_montant_scol(db_session, annee, niveau, montant=100000, montant_pri=90000, montant_sec=110000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, nouveau=True)
    _activer_annee(annee)

    data = StatistiquesService.get_etat_versements_scolarite()

    assert len(data) == 1
    # Prospectus 2026-2027 : le prescolaire garde le meme tarif nouveau/ancien.
    assert data[0]["MontantDu"] == 90000.0


def test_scolarite_surcharge_nouveau_appliquee_du_cp1_au_cm2(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau="CP1")
    famille = make_famille(db_session, ens_cat_primaire=True)
    eleve = make_eleve(db_session, famille, matricule="EL0002")
    make_montant_scol(db_session, annee, niveau, montant=100000, montant_pri=90000, montant_sec=110000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, nouveau=True)
    _activer_annee(annee)

    data = StatistiquesService.get_etat_versements_scolarite()

    assert len(data) == 1
    assert data[0]["MontantDu"] == 100000.0  # 90000 + 10000


# ─── Regression : reductions Cantine/Transport ne doivent pas etre comptees comme un versement reel ───

def test_cantine_reduction_totale_non_confondue_avec_versement_reel(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau="CM2")
    famille = make_famille(db_session, ens_cat_primaire=True)
    eleve = make_eleve(db_session, famille, matricule="EL0003")
    make_montant_cantine(db_session, annee, niveau, montant=20000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, cantine=True)
    _activer_annee(annee)

    db_session.add(VersementScol(
        IDFamille=famille.IdTFamille,
        IDEleve=eleve.IDEleve,
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        DateVers=date.today(),
        MontantCantine=20000,
        Reduction=True,
    ))
    db_session.commit()

    data = StatistiquesService.get_etat_versements_cantine()

    assert len(data) == 1
    item = data[0]
    assert item["MontantVerse"] == 0.0   # rien reellement encaisse
    assert item["Reduction"] == 20000.0
    assert item["Reste"] == 0.0
    assert item["Etat"] == "Payé"


def test_cantine_versement_partiel_et_reduction_partielle_cumulent_sur_le_reste(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau="CM2")
    famille = make_famille(db_session, ens_cat_primaire=True)
    eleve = make_eleve(db_session, famille, matricule="EL0004")
    make_montant_cantine(db_session, annee, niveau, montant=20000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, cantine=True)
    _activer_annee(annee)

    db_session.add(VersementScol(
        IDFamille=famille.IdTFamille, IDEleve=eleve.IDEleve, IDTAnneeScolaire=annee.IDTAnneeScolaire,
        DateVers=date.today(), MontantCantine=5000, Reduction=False,
    ))
    db_session.add(VersementScol(
        IDFamille=famille.IdTFamille, IDEleve=eleve.IDEleve, IDTAnneeScolaire=annee.IDTAnneeScolaire,
        DateVers=date.today(), MontantCantine=5000, Reduction=True,
    ))
    db_session.commit()

    data = StatistiquesService.get_etat_versements_cantine()

    assert len(data) == 1
    item = data[0]
    assert item["MontantVerse"] == 5000.0
    assert item["Reduction"] == 5000.0
    assert item["Reste"] == 10000.0  # 20000 - 5000 - 5000
    assert item["Etat"] == "Partiel"


def test_transport_reduction_totale_non_confondue_avec_versement_reel(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee, libelle_niveau="CM2")
    famille = make_famille(db_session, ens_cat_primaire=True)
    eleve = make_eleve(db_session, famille, matricule="EL0005")
    make_montant_transport(db_session, annee, niveau, montant=15000)
    make_inscription(db_session, annee, famille, eleve, niveau, classe, transport=True)
    _activer_annee(annee)

    db_session.add(VersementScol(
        IDFamille=famille.IdTFamille,
        IDEleve=eleve.IDEleve,
        IDTAnneeScolaire=annee.IDTAnneeScolaire,
        DateVers=date.today(),
        MontantVersTrans=15000,
        Reduction=True,
    ))
    db_session.commit()

    data = StatistiquesService.get_etat_versements_transport()

    assert len(data) == 1
    item = data[0]
    assert item["MontantVerse"] == 0.0
    assert item["Reduction"] == 15000.0
    assert item["Reste"] == 0.0
    assert item["Etat"] == "Payé"
