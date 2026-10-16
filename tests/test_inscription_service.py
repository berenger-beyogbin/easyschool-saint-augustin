from datetime import date

from app.session import AppSession
from models.eleve import Eleve
from models.inscription import TInscription
from models.versement_scol import VersementScol
from services.inscription_service import InscriptionService
from services.tarification_service import TarificationService
from services.versement_service import VersementService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_niveau_classe,
)


def _prepare(db_session, capacite=40):
    # Ces tests generiques d'inscription ne portent pas sur la campagne CJGA
    # 2026-2027 et ne doivent donc pas declencher ses frais obligatoires.
    annee = make_annee(db_session, libelle="2025-2026")
    niveau, classe = make_niveau_classe(db_session, annee)
    classe.Capacite = capacite
    db_session.commit()
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)
    return annee, niveau, classe


def test_inscription_refusee_si_eleve_sans_famille(db_session):
    annee, niveau, classe = _prepare(db_session)
    orphelin = Eleve(
        Matricule="SF-001", Nom="Sans", Prenoms="Famille",
        DateNaissance=date(2015, 1, 1), Sexe=1, IDFamille=None,
    )
    db_session.add(orphelin)
    db_session.commit()

    ok, message = InscriptionService.create_inscription({
        "IDEleve": orphelin.IDEleve,
        "IDNiveau": niveau.IDT_Niveau,
        "IDClasse": classe.IDTClasse,
    })

    assert not ok
    assert "famille" in message.lower()
    assert db_session.query(TInscription).count() == 0


def test_inscription_utilise_automatiquement_la_famille_de_leleve(db_session):
    annee, niveau, classe = _prepare(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-001")

    ok, message = InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve,
        "IDNiveau": niveau.IDT_Niveau,
        "IDClasse": classe.IDTClasse,
    })

    assert ok, message
    ins = db_session.query(TInscription).filter_by(IDEleve=eleve.IDEleve).one()
    assert ins.IDFamille == famille.IdTFamille


def test_inscription_rejette_famille_incoherente_dans_le_payload(db_session):
    annee, niveau, classe = _prepare(db_session)
    famille_reelle = make_famille(db_session, nom="Reelle", tel="0100000001")
    autre_famille = make_famille(db_session, nom="Autre", tel="0100000002")
    eleve = make_eleve(db_session, famille_reelle, matricule="EL-002")

    ok, message = InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve,
        "IDFamille": autre_famille.IdTFamille,
        "IDNiveau": niveau.IDT_Niveau,
        "IDClasse": classe.IDTClasse,
    })

    assert not ok
    assert "correspond" in message.lower()
    assert db_session.query(TInscription).count() == 0


def test_eleve_deja_inscrit_detecte_correctement(db_session):
    annee, niveau, classe = _prepare(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-003")

    assert InscriptionService.get_situation_scolaire_active(eleve.IDEleve, annee.IDTAnneeScolaire) is None

    InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })

    situation = InscriptionService.get_situation_scolaire_active(eleve.IDEleve, annee.IDTAnneeScolaire)
    assert situation is not None
    assert situation["id_classe"] == classe.IDTClasse
    assert situation["effectif"] == 1
    assert situation["capacite"] == classe.Capacite


def test_modification_inscription_existante_sans_creation_de_doublon(db_session):
    annee, niveau, classe = _prepare(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-004")
    InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })
    situation = InscriptionService.get_situation_scolaire_active(eleve.IDEleve, annee.IDTAnneeScolaire)

    # Une seconde création directe doit être refusée (doublon élève+année)
    ok_doublon, msg_doublon = InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })
    assert not ok_doublon
    assert "déjà" in msg_doublon.lower()

    # La modification passe elle par update_inscription, sans créer de ligne
    ok_update, msg_update = InscriptionService.update_inscription(
        situation["id_inscription"], {"IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse, "Nouveau": False}
    )
    assert ok_update, msg_update
    assert db_session.query(TInscription).filter_by(IDEleve=eleve.IDEleve).count() == 1


def test_controle_de_capacite_toujours_fonctionnel(db_session):
    annee, niveau, classe = _prepare(db_session, capacite=1)
    famille = make_famille(db_session)
    eleve1 = make_eleve(db_session, famille, matricule="EL-005")
    eleve2 = make_eleve(db_session, famille, matricule="EL-006")

    ok1, _ = InscriptionService.create_inscription({
        "IDEleve": eleve1.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })
    ok2, msg2 = InscriptionService.create_inscription({
        "IDEleve": eleve2.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })

    assert ok1
    assert not ok2
    assert "capacité maximale" in msg2


def test_fratrie_sans_reduction_automatique(db_session):
    """Le rang dans la fratrie ne modifie plus le tarif de scolarite."""
    annee, niveau, classe = _prepare(db_session)
    famille = make_famille(db_session)
    enfants = [make_eleve(db_session, famille, matricule=f"FRAT-{i}") for i in range(3)]
    for enfant in enfants:
        ok, msg = InscriptionService.create_inscription({
            "IDEleve": enfant.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
        })
        assert ok, msg

    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100_000, montant_non_affecte=100_000, statut_affectation="AFFECTE_ETAT",
    )
    assert montant == 100_000  # aucune reduction automatique du 3e enfant


def test_versement_lie_au_bon_eleve_et_a_la_bonne_famille(db_session):
    annee, niveau, classe = _prepare(db_session)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="EL-007")
    from tests.factories import make_montant_scol
    make_montant_scol(db_session, annee, niveau, montant_affecte=50_000, montant_non_affecte=50_000)
    InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })
    ins = db_session.query(TInscription).filter_by(IDEleve=eleve.IDEleve).one()
    assert ins.IDFamille == famille.IdTFamille

    ok, message, id_versement = VersementService.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve, id_famille=ins.IDFamille,
        date_v=date.today(), m_scol=20_000, m_trans=0, m_cant=0, m_autres=0,
    )

    assert ok, message
    versement = db_session.get(VersementScol, id_versement)
    assert versement.IDEleve == eleve.IDEleve
    assert versement.IDFamille == famille.IdTFamille


def _inscrire(db_session, matricule, tarif=0):
    annee, niveau, classe = _prepare(db_session)
    if tarif:
        from tests.factories import make_montant_scol
        make_montant_scol(db_session, annee, niveau, montant_affecte=tarif, montant_non_affecte=tarif)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule=matricule)
    InscriptionService.create_inscription({
        "IDEleve": eleve.IDEleve, "IDNiveau": niveau.IDT_Niveau, "IDClasse": classe.IDTClasse,
    })
    ins = db_session.query(TInscription).filter_by(IDEleve=eleve.IDEleve).one()
    return annee, niveau, eleve, ins


def test_suppression_inscription_sans_versement(db_session):
    annee, niveau, eleve, ins = _inscrire(db_session, "EL-DEL1")
    id_ins = ins.IDTInscription

    ok, message = InscriptionService.supprimer_inscription(id_ins, "Erreur de saisie")

    assert ok, message
    db_session.expire_all()
    assert db_session.query(TInscription).filter_by(IDTInscription=id_ins).count() == 0
    assert db_session.get(Eleve, eleve.IDEleve) is not None


def test_suppression_inscription_exige_un_motif(db_session):
    annee, niveau, eleve, ins = _inscrire(db_session, "EL-DEL2")

    ok, message = InscriptionService.supprimer_inscription(ins.IDTInscription, "  ")

    assert not ok
    assert "motif" in message.lower()
    assert db_session.query(TInscription).count() == 1


def test_suppression_inscription_possible_apres_annulation_de_tous_les_versements(db_session):
    annee, niveau, eleve, ins = _inscrire(db_session, "EL-DEL3", tarif=50_000)
    ok, message, id_versement = VersementService.create_versement(
        id_annee=annee.IDTAnneeScolaire, id_eleve=eleve.IDEleve, id_famille=ins.IDFamille,
        date_v=date.today(), m_scol=20_000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok, message

    ok, message = InscriptionService.supprimer_inscription(ins.IDTInscription, "Erreur")
    assert not ok
    assert "versement" in message.lower()

    ok, message = VersementService.annuler_versement(id_versement, "Erreur")
    assert ok, message
    ok, message = InscriptionService.supprimer_inscription(ins.IDTInscription, "Erreur")
    assert ok, message
    db_session.expire_all()
    assert db_session.query(TInscription).count() == 0
