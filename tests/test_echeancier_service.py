from datetime import date

from services.echeancier_service import EcheancierService


def test_nouveau_primaire_premiere_tranche_et_prochaine_echeance():
    tranches = EcheancierService._fallback(
        type("Annee", (), {"Libelle": "2026-2027"})(),
        EcheancierService.SCOLARITE,
        EcheancierService.NOUVEAU_PRIMAIRE,
    )
    situation = EcheancierService.situation(
        tranches, 125000, date(2026, 7, 15), date(2026, 10, 1)
    )

    assert situation["exigible"] == 125000
    assert situation["statut"] == "A JOUR"
    assert situation["prochaine_echeance"]["date_effective"] == date(2026, 11, 30)


def test_ancien_primaire_est_en_retard_apres_le_30_novembre():
    tranches = EcheancierService._fallback(
        type("Annee", (), {"Libelle": "2026-2027"})(),
        EcheancierService.SCOLARITE,
        EcheancierService.ANCIEN_PRIMAIRE,
    )
    situation = EcheancierService.situation(
        tranches, 115000, date(2026, 7, 15), date(2026, 12, 1)
    )

    assert situation["exigible"] == 155000
    assert situation["reste_exigible"] == 40000
    assert situation["statut"] == "EN RETARD"


def test_prescolaire_nouveau_garde_echeancier_total_170000():
    tranches = EcheancierService._fallback(
        type("Annee", (), {"Libelle": "2026-2027"})(),
        EcheancierService.SCOLARITE,
        EcheancierService.PRESCOLAIRE,
    )
    situation = EcheancierService.situation(
        tranches, 0, date(2026, 7, 15), date(2026, 7, 15)
    )

    assert situation["total_echeancier"] == 170000
    assert situation["exigible"] == 100000


def test_transport_et_cantine_ont_les_echeances_2027():
    annee = type("Annee", (), {"Libelle": "2026-2027"})()
    for type_frais in (EcheancierService.TRANSPORT, EcheancierService.CANTINE):
        tranches = EcheancierService._fallback(
            annee, type_frais, EcheancierService.TOUS
        )
        assert [tranche["montant"] for tranche in tranches] == [50000, 40000, 30000]
        assert tranches[1]["date_echeance"] == date(2027, 1, 31)
        assert tranches[2]["date_echeance"] == date(2027, 3, 31)

