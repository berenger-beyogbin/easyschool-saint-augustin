from utils.print_helpers import format_fcfa, payment_status_label


def test_format_fcfa_is_consistent():
    assert format_fcfa(150000) == "150 000 FCFA"
    assert format_fcfa(0) == "0 FCFA"
    assert format_fcfa(None) == "0 FCFA"


def test_payment_status_label_keeps_three_distinct_states():
    assert payment_status_label("Payé") == "Soldé"
    assert payment_status_label("Partiel") == "Partiel"
    assert payment_status_label("Impayé") == "Impayé"
    assert payment_status_label(None) == "Impayé"
