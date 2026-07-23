from utils.receipt_printer import _texte_institutionnel_redondant


def test_receipt_header_avoids_repeating_institution_type():
    assert _texte_institutionnel_redondant(
        "École primaire catholique",
        "École Primaire Catholique Saint Augustin Abobo-té",
    ) is True
    assert _texte_institutionnel_redondant(
        "Enseignement primaire",
        "Groupe scolaire Saint Augustin",
    ) is False
