"""Tests cibles pour les correctifs apportes au module Inscriptions/Eleves/Familles :

1. EleveService.update_eleve synchronise IDFamille sur les inscriptions existantes
   et bloque la deliaison si des inscriptions y sont rattachees.
2. FamilleService.delete_famille verifie aussi TInscription.IDFamille (pas seulement Eleve.IDFamille).
3. InscriptionService.delete_inscription (desinscription), bloquee si versements/annee cloturee.
4. InscriptionService.update_inscription declenche le recalcul de la ventilation analytique
   et avertit en cas de trop-percu suite a un changement de niveau.
"""
from datetime import date

from app.session import AppSession
from models.eleve import Eleve
from models.famille import TFamille
from models.inscription import TInscription
from services.eleve_service import EleveService
from services.famille_service import FamilleService
from services.inscription_service import InscriptionService
from services.ventilation_service import VentilationService
from services.versement_service import VersementService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_montant_scol,
    make_niveau_classe,
    make_prestation,
    make_tarif_niveau,
)


def _set_eleves_permission_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 4000,
            "Login": "eleves_correctif",
            "Nom": "Eleves",
            "ProfilCode": "ELEVES_WRITE",
            "ProfilLibelle": "Eleves ecriture",
            "IsAdmin": False,
        },
        permissions={"SCOLARITE_ELEVES"},
    )


def _set_inscriptions_permission_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 4001,
            "Login": "inscriptions_correctif",
            "Nom": "Inscriptions",
            "ProfilCode": "INSCRIPTIONS_WRITE",
            "ProfilLibelle": "Inscriptions ecriture",
            "IsAdmin": False,
        },
        permissions={"SCOLARITE_INSCRIPTIONS"},
    )


def _set_versements_permission_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 4002,
            "Login": "versements_correctif",
            "Nom": "Versements",
            "ProfilCode": "CAISSE",
            "ProfilLibelle": "Caisse",
            "IsAdmin": False,
        },
        permissions={"SCOLARITE_VERSEMENTS"},
    )


def _setup_inscription(db_session):
    """Contexte de base : une inscription active pour un eleve, sans versement."""
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-CORR-001")
    make_montant_scol(db_session, annee, niveau)
    inscription = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    return annee, niveau, classe, famille, eleve, inscription


# ─── Correctif 1 : synchronisation Eleve.IDFamille <-> TInscription.IDFamille ──


def test_update_eleve_syncs_family_to_existing_inscriptions(db_session):
    annee, niveau, classe, famille_a, eleve, inscription = _setup_inscription(db_session)
    famille_b = make_famille(db_session, nom="Famille B", tel="0722222222")
    _set_eleves_permission_user()

    ok, msg = EleveService.update_eleve(eleve.IDEleve, {
        "Matricule": eleve.Matricule,
        "Nom": eleve.Nom,
        "Prenoms": eleve.Prenoms,
        "DateNaissance": eleve.DateNaissance,
        "Sexe": eleve.Sexe,
        "IDFamille": famille_b.IdTFamille,
    })

    db_session.expire_all()
    assert ok is True, msg
    assert db_session.get(Eleve, eleve.IDEleve).IDFamille == famille_b.IdTFamille
    assert db_session.get(TInscription, inscription.IDTInscription).IDFamille == famille_b.IdTFamille


def test_update_eleve_blocks_unlinking_family_with_existing_inscriptions(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    _set_eleves_permission_user()

    ok, msg = EleveService.update_eleve(eleve.IDEleve, {
        "Matricule": eleve.Matricule,
        "Nom": eleve.Nom,
        "Prenoms": eleve.Prenoms,
        "DateNaissance": eleve.DateNaissance,
        "Sexe": eleve.Sexe,
        "IDFamille": None,
    })

    db_session.expire_all()
    assert ok is False
    assert "famille" in msg.lower()
    assert db_session.get(Eleve, eleve.IDEleve).IDFamille == famille.IdTFamille
    assert db_session.get(TInscription, inscription.IDTInscription).IDFamille == famille.IdTFamille


# ─── Correctif 2 : delete_famille verifie aussi TInscription.IDFamille ─────────


def test_delete_famille_refused_when_only_inscription_references_it(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    autre_famille = make_famille(db_session, nom="Autre Famille", tel="0733333333")
    # Simule une desynchronisation historique : l'eleve est reaffecte directement en
    # base a une autre famille, mais l'inscription existante reference toujours
    # l'originale (situation que le correctif d'update_eleve empeche desormais,
    # mais qui peut deja exister sur des donnees anciennes).
    eleve.IDFamille = autre_famille.IdTFamille
    db_session.commit()
    _set_eleves_permission_user()

    ok, msg = FamilleService.delete_famille(famille.IdTFamille)

    db_session.expire_all()
    assert ok is False
    assert "inscription" in msg.lower()
    assert db_session.get(TFamille, famille.IdTFamille) is not None


def test_delete_famille_still_refused_when_eleves_directly_attached(db_session):
    """Non-regression : le garde-fou historique (Eleve.IDFamille) reste actif."""
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    _set_eleves_permission_user()

    ok, msg = FamilleService.delete_famille(famille.IdTFamille)

    db_session.expire_all()
    assert ok is False
    assert "élève" in msg.lower() or "eleve" in msg.lower()
    assert db_session.get(TFamille, famille.IdTFamille) is not None


# ─── Correctif 3 : InscriptionService.delete_inscription (desinscription) ─────


def test_delete_inscription_succeeds_when_no_versement(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    id_inscription = inscription.IDTInscription  # capture avant suppression : l'objet
    # ORM ne doit plus etre touche une fois sa ligne supprimee ailleurs.
    _set_inscriptions_permission_user()

    ok, msg = InscriptionService.delete_inscription(id_inscription)

    assert ok is True, msg
    assert db_session.query(TInscription).filter_by(
        IDTInscription=id_inscription
    ).first() is None


def test_delete_inscription_blocked_when_versement_exists(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    _set_versements_permission_user()
    ok, msg, versement_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=10000, m_trans=0, m_cant=0,
    )
    assert ok is True, msg

    _set_inscriptions_permission_user()
    ok, msg = InscriptionService.delete_inscription(inscription.IDTInscription)

    db_session.expire_all()
    assert ok is False
    assert "versement" in msg.lower()
    assert db_session.get(TInscription, inscription.IDTInscription) is not None


def test_delete_inscription_blocked_when_annee_cloturee(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    annee.Cloturer = True
    db_session.commit()
    _set_inscriptions_permission_user()

    ok, msg = InscriptionService.delete_inscription(inscription.IDTInscription)

    db_session.expire_all()
    assert ok is False
    assert "clôtur" in msg.lower()
    assert db_session.get(TInscription, inscription.IDTInscription) is not None


def test_delete_inscription_requires_inscriptions_permission(db_session):
    annee, niveau, classe, famille, eleve, inscription = _setup_inscription(db_session)
    _set_eleves_permission_user()  # permission SCOLARITE_ELEVES, pas SCOLARITE_INSCRIPTIONS

    ok, msg = InscriptionService.delete_inscription(inscription.IDTInscription)

    db_session.expire_all()
    assert ok is False
    assert "SCOLARITE_INSCRIPTIONS" in msg
    assert db_session.get(TInscription, inscription.IDTInscription) is not None


# ─── Correctif 4 : update_inscription -> recalcul ventilation + alerte trop-percu ──


def test_update_inscription_recalculates_ventilation_after_niveau_change(db_session):
    annee = make_annee(db_session)
    niveau_a, classe_a = make_niveau_classe(db_session, annee, libelle_niveau="CM2")
    niveau_b, classe_b = make_niveau_classe(db_session, annee, libelle_niveau="CM1")
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-VENT-001")
    make_montant_scol(db_session, annee, niveau_a, montant=100000, montant_pri=100000, montant_sec=100000)
    make_montant_scol(db_session, annee, niveau_b, montant=100000, montant_pri=100000, montant_sec=100000)
    prestation = make_prestation(db_session, "TENUE", 10000)
    make_tarif_niveau(db_session, annee, niveau_b, prestation, montant_annuel=25000)
    inscription = make_inscription(db_session, annee, famille, eleve, niveau_a, classe_a)

    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    _set_versements_permission_user()
    ok, msg, _ = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=100000, m_trans=0, m_cant=0,
    )
    assert ok is True, msg

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    par_code = {v["code"]: v for v in ventilations}
    assert par_code["TENUE"]["montant_theorique"] == 10000.0  # pas encore la surcharge du niveau B

    _set_inscriptions_permission_user()
    ok, msg = InscriptionService.update_inscription(inscription.IDTInscription, {
        "IDNiveau": niveau_b.IDT_Niveau,
        "IDClasse": classe_b.IDTClasse,
    })

    db_session.expire_all()
    assert ok is True, msg

    ventilations = VentilationService.get_student_ventilations(eleve.IDEleve, annee.IDTAnneeScolaire)
    par_code = {v["code"]: v for v in ventilations}
    # La ventilation reflete desormais la surcharge tarifaire du NOUVEAU niveau (25000),
    # preuve que update_inscription a bien declenche un recalcul (sinon on garderait 10000).
    assert par_code["TENUE"]["montant_theorique"] == 25000.0


def test_update_inscription_warns_on_trop_percu_after_niveau_change(db_session):
    annee = make_annee(db_session)
    niveau_cher, classe_cher = make_niveau_classe(db_session, annee, libelle_niveau="CM2")
    niveau_moins_cher, classe_moins_cher = make_niveau_classe(db_session, annee, libelle_niveau="CP1")
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-VENT-002")
    make_montant_scol(db_session, annee, niveau_cher, montant=100000, montant_pri=100000, montant_sec=100000)
    make_montant_scol(db_session, annee, niveau_moins_cher, montant=40000, montant_pri=40000, montant_sec=40000)
    inscription = make_inscription(db_session, annee, famille, eleve, niveau_cher, classe_cher)

    AppSession._active_annee_id = annee.IDTAnneeScolaire
    AppSession._active_annee_libelle = annee.Libelle
    _set_versements_permission_user()
    ok, msg, _ = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=100000, m_trans=0, m_cant=0,
    )
    assert ok is True, msg

    _set_inscriptions_permission_user()
    ok, msg = InscriptionService.update_inscription(inscription.IDTInscription, {
        "IDNiveau": niveau_moins_cher.IDT_Niveau,
        "IDClasse": classe_moins_cher.IDTClasse,
    })

    # Le changement reste autorise (pas de blocage), mais un avertissement de trop-percu
    # doit signaler que 100000 F ont deja ete verses pour un du qui n'est plus que de 40000 F.
    assert ok is True, msg
    assert "trop-per" in msg.lower()


def test_update_inscription_no_warning_when_no_versement(db_session):
    """Non-regression : sans versement prealable, aucun avertissement de trop-percu."""
    annee, niveau_a, classe_a, famille, eleve, inscription = _setup_inscription(db_session)
    niveau_b, classe_b = make_niveau_classe(db_session, annee, libelle_niveau="CP1")
    make_montant_scol(db_session, annee, niveau_b, montant=40000, montant_pri=40000, montant_sec=40000)
    _set_inscriptions_permission_user()

    ok, msg = InscriptionService.update_inscription(inscription.IDTInscription, {
        "IDNiveau": niveau_b.IDT_Niveau,
        "IDClasse": classe_b.IDTClasse,
    })

    assert ok is True, msg
    assert "trop-per" not in msg.lower()
