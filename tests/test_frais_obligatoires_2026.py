from datetime import date

from app.session import AppSession
from models.inscription import TInscription
from services.inscription_autres_frais_service import InscriptionAutresFraisService
from services.inscription_service import InscriptionService
from services.versement_service import VersementService
from tests.factories import (
    make_annee, make_eleve, make_famille, make_montant_scol,
    make_niveau_classe,
)


def _inscrire(db_session, *, sexe=1, nouveau=True, statut="AFFECTE_ETAT"):
    annee = make_annee(db_session, "2026-2027")
    niveau, classe = make_niveau_classe(db_session, annee, "6e")
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule=f"FRAIS-{sexe}-{int(nouveau)}")
    eleve.Sexe = sexe
    db_session.commit()
    make_montant_scol(db_session, annee, niveau, 120000, 190000)
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)
    ok, msg = InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve,
        "IDNiveau": niveau.IDT_Niveau,
        "IDClasse": classe.IDTClasse,
        "Nouveau": nouveau,
        "StatutAffectation": statut,
    })
    assert ok, msg
    inscription = db_session.query(TInscription).filter_by(IDEleve=eleve.IDEleve).one()
    return annee, famille, eleve, inscription


def test_nouvelle_fille_recoit_tenue_et_fournitures(db_session):
    _annee, _famille, _eleve, inscription = _inscrire(db_session, sexe=2, nouveau=True)
    frais = InscriptionAutresFraisService.get_frais_coches(inscription.IDTInscription)
    assert {f["CodeFraisSnapshot"] for f in frais} == {"TENUE_F2", "FOUR_NOUV"}
    assert sum(float(f["MontantApplique"]) for f in frais) == 37000
    assert all(f["Obligatoire"] for f in frais)


def test_ancien_eleve_recoit_uniquement_les_feuilles(db_session):
    _annee, _famille, _eleve, inscription = _inscrire(db_session, nouveau=False)
    frais = InscriptionAutresFraisService.get_frais_coches(inscription.IDTInscription)
    assert [(f["CodeFraisSnapshot"], float(f["MontantApplique"])) for f in frais] == [
        ("FEUIL_ANC", 10000.0)
    ]


def test_scolarite_partielle_refusee_tant_que_frais_obligatoires_non_inclus(db_session):
    annee, famille, eleve, _inscription = _inscrire(db_session, nouveau=False)
    ok, msg, _id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=50000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert not ok
    assert "obligatoires" in msg


def test_scolarite_reste_partielle_apres_paiement_integral_des_autres_frais(db_session):
    annee, famille, eleve, inscription = _inscrire(db_session, nouveau=False)
    frais = InscriptionAutresFraisService.get_frais_impayes(inscription.IDTInscription)
    ids = [f["IDInscriptionAutresFrais"] for f in frais]
    ok, msg, _id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=50000, m_trans=0, m_cant=0, m_autres=10000,
        ids_autres_frais=ids,
    )
    assert ok, msg
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_reste"] == 70000
    assert fin["autres_reste"] == 0


def test_reduction_scolarite_acceptee_meme_si_frais_obligatoires_impayes(db_session):
    annee, famille, eleve, _inscription = _inscrire(db_session, nouveau=False)

    ok, msg, _id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=15000, m_trans=0, m_cant=0, m_autres=0,
        reduction=True,
    )

    assert ok, msg
    fin = VersementService.get_infos_financieres_eleve(
        annee.IDTAnneeScolaire, eleve.IDEleve
    )
    assert fin["scol_reste"] == 105000
    assert fin["autres_reste"] == 10000


def test_reduction_refusee_si_un_frais_annexe_est_fourni(db_session):
    annee, famille, eleve, inscription = _inscrire(db_session, nouveau=False)
    frais = InscriptionAutresFraisService.get_frais_impayes(inscription.IDTInscription)

    ok, msg, _id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=15000, m_trans=0, m_cant=0, m_autres=10000,
        reduction=True,
        ids_autres_frais=[frais[0]["IDInscriptionAutresFrais"]],
    )

    assert not ok
    assert "uniquement aux frais de scolarite" in msg
