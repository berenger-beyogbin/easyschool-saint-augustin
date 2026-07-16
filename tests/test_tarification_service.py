from services.tarification_service import TarificationService
from tests.factories import make_annee, make_niveau_classe, make_famille, make_eleve, make_inscription


def test_montant_affecte_par_defaut():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=80000,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=False, nouveau=False,
        rang_famille=1, nb_enfants_famille=1,
    )
    assert montant == 100000


def test_montant_non_affecte():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=80000,
        statut_affectation="NON_AFFECTE_ETAT", ebrie_abobote=False, nouveau=False,
        rang_famille=1, nb_enfants_famille=1,
    )
    assert montant == 80000


def test_reduction_ebrie_abobote():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=True, nouveau=False,
        rang_famille=1, nb_enfants_famille=1,
    )
    assert montant == 90000


def test_surcharge_nouvel_eleve_affecte():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=False, nouveau=True,
        rang_famille=1, nb_enfants_famille=1,
    )
    assert montant == 115000


def test_pas_de_surcharge_nouvel_eleve_non_affecte():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=0, montant_non_affecte=80000,
        statut_affectation="NON_AFFECTE_ETAT", ebrie_abobote=False, nouveau=True,
        rang_famille=1, nb_enfants_famille=1,
    )
    assert montant == 80000


def test_reduction_troisieme_enfant():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=False, nouveau=False,
        rang_famille=3, nb_enfants_famille=3,
    )
    assert montant == 90000


def test_pas_de_reduction_avant_le_troisieme_enfant():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=False, nouveau=False,
        rang_famille=2, nb_enfants_famille=2,
    )
    assert montant == 100000


def test_montant_ne_descend_jamais_sous_zero():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=5000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=True, nouveau=False,
        rang_famille=3, nb_enfants_famille=3,
    )
    assert montant == 0


def test_cumul_ebrie_et_troisieme_enfant():
    montant = TarificationService.calculer_scolarite_due(
        montant_affecte=100000, montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT", ebrie_abobote=True, nouveau=False,
        rang_famille=3, nb_enfants_famille=3,
    )
    assert montant == 80000


def test_rang_famille_coherent_entre_les_deux_methodes(db_session):
    """get_rang_famille_pour_inscription (cible unique) et
    get_rangs_famille_par_eleve (bulk) doivent donner le meme rang."""
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleves = [make_eleve(db_session, famille, matricule=f"TARIF{i}") for i in range(3)]
    inscriptions = [
        make_inscription(db_session, annee, famille, eleve, niveau, classe)
        for eleve in eleves
    ]

    rangs_bulk = TarificationService.get_rangs_famille_par_eleve(db_session, annee.IDTAnneeScolaire)

    for i, ins in enumerate(inscriptions):
        rang_cible, nb_cible = TarificationService.get_rang_famille_pour_inscription(
            db_session, ins, annee.IDTAnneeScolaire
        )
        rang_bulk, nb_bulk = rangs_bulk[ins.IDEleve]
        assert rang_cible == rang_bulk == i + 1
        assert nb_cible == nb_bulk == 3


def test_rang_famille_sans_famille_renvoie_un_seul_enfant(db_session):
    annee = make_annee(db_session)
    niveau, classe = make_niveau_classe(db_session, annee)
    famille = make_famille(db_session)
    eleve = make_eleve(db_session, famille, matricule="TARIFSOLO")
    ins = make_inscription(db_session, annee, famille, eleve, niveau, classe)
    ins.IDFamille = None

    rang, nb = TarificationService.get_rang_famille_pour_inscription(db_session, ins, annee.IDTAnneeScolaire)
    assert (rang, nb) == (1, 1)
