from services.tarification_service import TarificationService


def test_montant_affecte():
    assert TarificationService.calculer_scolarite_due(
        montant_affecte=120000,
        montant_non_affecte=190000,
        statut_affectation="AFFECTE_ETAT",
    ) == 120000


def test_montant_non_affecte():
    assert TarificationService.calculer_scolarite_due(
        montant_affecte=120000,
        montant_non_affecte=190000,
        statut_affectation="NON_AFFECTE_ETAT",
    ) == 190000


def test_aucune_ancienne_reduction_ou_surcharge_n_est_appliquee():
    # Le moteur ne recoit plus le profil Ebrie, le rang familial ni le statut
    # nouveau : seul le tarif catalogue selon l'affectation est retourne.
    assert TarificationService.calculer_scolarite_due(
        montant_affecte=120000,
        montant_non_affecte=190000,
        statut_affectation="AFFECTE_ETAT",
    ) == 120000


def test_montant_negatif_est_ramene_a_zero():
    assert TarificationService.calculer_scolarite_due(
        montant_affecte=-1,
        montant_non_affecte=0,
        statut_affectation="AFFECTE_ETAT",
    ) == 0
