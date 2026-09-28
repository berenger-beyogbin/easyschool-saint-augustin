from services.classe_service import normaliser_libelle_classe


def test_suffixes_alphabetiques_deviennent_numeriques():
    assert normaliser_libelle_classe("6E A") == "6E 1"
    assert normaliser_libelle_classe("6e b") == "6E 2"
    assert normaliser_libelle_classe("5E-Z") == "5E 26"


def test_suffixes_deja_numeriques_restent_inchanges():
    assert normaliser_libelle_classe("6E 1") == "6E 1"
    assert normaliser_libelle_classe("  5e   2  ") == "5E 2"
