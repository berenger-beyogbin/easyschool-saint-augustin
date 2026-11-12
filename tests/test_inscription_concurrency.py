from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.session import AppSession
from models.classe import TClasse
from models.inscription import TInscription
from services.inscription_service import InscriptionService
from tests.factories import (
    make_annee,
    make_eleve,
    make_famille,
    make_inscription,
    make_niveau_classe,
)


def _run_concurrently(operation, values):
    barrier = Barrier(len(values))

    def synchronized(value):
        barrier.wait()
        return operation(value)

    with ThreadPoolExecutor(max_workers=len(values)) as executor:
        return list(executor.map(synchronized, values))


def test_concurrent_creations_do_not_exceed_class_capacity(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    classe.Capacite = 1
    famille = make_famille(db_session)
    eleves = [
        make_eleve(db_session, famille, matricule="CONC-CREATE-1"),
        make_eleve(db_session, famille, matricule="CONC-CREATE-2"),
    ]
    db_session.commit()
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)
    famille_id = famille.IdTFamille
    niveau_id = niveau.IDT_Niveau
    classe_id = classe.IDTClasse
    eleve_ids = [eleve.IDEleve for eleve in eleves]

    def create(eleve_id):
        return InscriptionService.create_inscription({
            "IDEleve": eleve_id,
            "IDFamille": famille_id,
            "IDNiveau": niveau_id,
            "IDClasse": classe_id,
        })

    results = _run_concurrently(create, eleve_ids)

    assert sum(ok for ok, _ in results) == 1
    assert any("capacité maximale" in message for ok, message in results if not ok)
    assert db_session.query(TInscription).filter_by(IDClasse=classe_id).count() == 1


def test_concurrent_updates_do_not_exceed_target_class_capacity(db_session):
    annee = make_annee(db_session)
    niveau, classe_cible = make_niveau_classe(db_session, annee)
    classe_cible.Capacite = 1
    classes_sources = [
        TClasse(
            LibClasse=f"CM2 Source {suffix}",
            IDT_Niveau=niveau.IDT_Niveau,
            IDAnneeScolaire=annee.IDTAnneeScolaire,
            Capacite=40,
        )
        for suffix in ("A", "B")
    ]
    db_session.add_all(classes_sources)
    famille = make_famille(db_session)
    eleves = [
        make_eleve(db_session, famille, matricule="CONC-UPDATE-1"),
        make_eleve(db_session, famille, matricule="CONC-UPDATE-2"),
    ]
    inscriptions = [
        make_inscription(db_session, annee, famille, eleve, niveau, classe_source)
        for eleve, classe_source in zip(eleves, classes_sources)
    ]
    db_session.commit()
    AppSession.set_active_annee(annee.IDTAnneeScolaire, annee.Libelle)
    niveau_id = niveau.IDT_Niveau
    classe_cible_id = classe_cible.IDTClasse
    inscription_ids = [item.IDTInscription for item in inscriptions]

    def move(inscription_id):
        return InscriptionService.update_inscription(inscription_id, {
            "IDNiveau": niveau_id,
            "IDClasse": classe_cible_id,
        })

    results = _run_concurrently(move, inscription_ids)

    assert sum(ok for ok, _ in results) == 1
    assert any("capacité maximale" in message for ok, message in results if not ok)
    assert db_session.query(TInscription).filter_by(IDClasse=classe_cible_id).count() == 1
