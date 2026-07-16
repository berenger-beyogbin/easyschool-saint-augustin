from datetime import date

from services.versement_service import VersementService
from services.inscription_autres_frais_service import InscriptionAutresFraisService
from tests.factories import (
    make_annee, make_niveau_classe, make_famille, make_eleve,
    make_inscription, make_montant_scol, make_montant_transport, make_montant_cantine,
    make_inscription_autres_frais,
)


def _setup_base(db_session, ebrie_abobote=False, nouveau=False, **ins_opts):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session, ebrie_abobote=ebrie_abobote)
    eleve = make_eleve(db_session, famille, matricule="EL0001")
    make_montant_scol(db_session, annee, niveau, montant_affecte=100000, montant_non_affecte=80000)
    ins = make_inscription(db_session, annee, famille, eleve, niveau, classe, nouveau=nouveau, **ins_opts)
    return annee, niveau, classe, famille, eleve, ins


def test_scol_due_uses_affecte_rate_by_default(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 100000.0


def test_scol_due_uses_non_affecte_rate(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(
        db_session, statut_affectation="NON_AFFECTE_ETAT",
    )
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 80000.0


def test_ebrie_abobote_reduction_applied(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, ebrie_abobote=True)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 90000.0  # 100000 - 10000


def test_nouveau_eleve_affecte_surcharge_applied(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session, nouveau=True)
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 115000.0  # 100000 + 15000 (affecte de l'Etat)


def test_nouveau_eleve_non_affecte_pas_de_surcharge(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(
        db_session, nouveau=True, statut_affectation="NON_AFFECTE_ETAT",
    )
    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_due"] == 80000.0  # pas de surcharge "nouveau" pour un non affecte


def test_third_child_of_family_gets_reduction(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    make_montant_scol(db_session, annee, niveau, montant_affecte=100000, montant_non_affecte=80000)

    eleve1 = make_eleve(db_session, famille, matricule="EL0001", nom="Enfant1")
    eleve2 = make_eleve(db_session, famille, matricule="EL0002", nom="Enfant2")
    eleve3 = make_eleve(db_session, famille, matricule="EL0003", nom="Enfant3")

    make_inscription(db_session, annee, famille, eleve1, niveau, classe)
    make_inscription(db_session, annee, famille, eleve2, niveau, classe)
    make_inscription(db_session, annee, famille, eleve3, niveau, classe)

    fin1 = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve1.IDEleve)
    fin3 = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve3.IDEleve)

    assert fin1["scol_due"] == 100000.0      # 1er enfant : pas de reduction
    assert fin3["scol_due"] == 90000.0       # 3e enfant : -10000


def test_create_versement_rejects_amount_above_reste(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=105000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "depasse" in msg.lower()
    assert new_id is None


def test_create_versement_success_updates_paid_amount(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=50000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is True
    assert new_id is not None

    fin = VersementService.get_infos_financieres_eleve(annee.IDTAnneeScolaire, eleve.IDEleve)
    assert fin["scol_paye"] == 50000.0
    assert fin["scol_reste"] == 50000.0  # 100000 - 50000


def test_create_versement_rejects_negative_amount(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=-100, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "negatifs" in msg.lower()


def test_create_versement_rejects_when_annee_cloturee(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    annee.Cloturer = True
    db_session.commit()

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=10000, m_trans=0, m_cant=0, m_autres=0,
    )
    assert ok is False
    assert "cloturee" in msg.lower()


def test_autres_frais_payment_removes_item_from_impayes_list(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ligne = make_inscription_autres_frais(db_session, ins, montant=6000)

    impayes_avant = InscriptionAutresFraisService.get_frais_impayes(ins.IDTInscription)
    assert len(impayes_avant) == 1

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=6000,
        ids_autres_frais=[ligne.IDInscriptionAutresFrais],
    )
    assert ok is True, msg

    impayes_apres = InscriptionAutresFraisService.get_frais_impayes(ins.IDTInscription)
    assert impayes_apres == []


def test_autres_frais_double_paiement_rejete(db_session):
    """Le reglement d'un meme frais annexe deux fois est rejete, que ce soit par le
    garde-fou global (reste a payer) ou par le controle explicite de frais deja regle."""
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ligne = make_inscription_autres_frais(db_session, ins, montant=6000)

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=6000,
        ids_autres_frais=[ligne.IDInscriptionAutresFrais],
    )
    assert ok is True

    ok2, msg2, new_id2 = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=6000,
        ids_autres_frais=[ligne.IDInscriptionAutresFrais],
    )
    assert ok2 is False
    assert "depasse" in msg2.lower() or "deja" in msg2.lower()
    assert new_id2 is None


def test_autres_frais_deja_regle_rejete_explicitement(db_session):
    """Meme si le reste global le permettrait (nouveau frais ajoute entre-temps), un frais
    annexe deja regle par un versement precedent ne peut pas etre selectionne a nouveau."""
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ligne_a = make_inscription_autres_frais(db_session, ins, code="TENUE", montant=6000)

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=6000,
        ids_autres_frais=[ligne_a.IDInscriptionAutresFrais],
    )
    assert ok is True

    # Un nouveau frais est ajoute apres coup : le reste global remonte a 6000 F,
    # ce qui suffirait a couvrir une nouvelle tentative sur le frais deja regle.
    make_inscription_autres_frais(db_session, ins, code="COACH", montant=6000)

    ok2, msg2, new_id2 = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=6000,
        ids_autres_frais=[ligne_a.IDInscriptionAutresFrais],
    )
    assert ok2 is False
    assert "deja" in msg2.lower()
    assert new_id2 is None


def test_autres_frais_montant_incoherent_rejete(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
    ligne = make_inscription_autres_frais(db_session, ins, montant=6000)

    ok, msg, new_id = VersementService.create_versement(
        annee.IDTAnneeScolaire, eleve.IDEleve, famille.IdTFamille,
        date.today(), m_scol=0, m_trans=0, m_cant=0, m_autres=3000,
        ids_autres_frais=[ligne.IDInscriptionAutresFrais],
    )
    assert ok is False
    assert "correspond" in msg.lower()


def test_delete_versement_blocked_when_annee_cloturee(db_session):
    annee, niveau, classe, famille, eleve, ins = _setup_base(db_session)
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
