from datetime import date

from openpyxl import Workbook

from services.eleve_import_service import EleveImportService


def _write_workbook(path, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "A"
    sheet.append([
        "photo", "CODE", "MATRICULE", "NOM ET PRENOMS", "DATE NAISSANCE",
        "REDOUBLE", "LV2", "STATUT", "SEXE",
    ])
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_read_xlsx_normalise_une_ligne(tmp_path):
    path = tmp_path / "eleves.xlsx"
    _write_workbook(path, [[
        None, "abc123", "MAT-1", "KOUASSI JEAN MARC", date(2012, 5, 4),
        "R", "Espagnol", "AFF", "M",
    ]])

    rows = EleveImportService.read_xlsx(str(path))

    assert len(rows) == 1
    assert rows[0].nom == "KOUASSI"
    assert rows[0].prenoms == "JEAN MARC"
    assert rows[0].date_naissance == date(2012, 5, 4)
    assert rows[0].sexe == 1
    assert rows[0].deuxieme_langue == "ESPAGNOL"
    assert rows[0].statut_source == "AFFECTE_ETAT"
    assert rows[0].redoublant_source is True


def test_read_xlsx_signale_date_et_sexe_manquants(tmp_path):
    path = tmp_path / "eleves_invalides.xlsx"
    _write_workbook(path, [[None, "abc123", None, "KOUASSI JEAN", None, None, "Null", "NAFF", None]])

    row = EleveImportService.read_xlsx(str(path))[0]

    assert "Date de naissance manquante ou invalide" in row.errors
    assert "Sexe manquant ou invalide" in row.errors
    assert row.deuxieme_langue is None
    assert row.statut_source == "NON_AFFECTE_ETAT"


def test_simulation_detecte_les_matricules_nationaux_doubles(tmp_path):
    path = tmp_path / "doublons.xlsx"
    _write_workbook(path, [
        [None, "code-1", "NAT-1", "KOUASSI JEAN", date(2012, 5, 4), "NON", None, "AFF", "M"],
        [None, "code-2", "NAT-1", "YAO MARIE", date(2013, 6, 5), "NON", None, "AFF", "F"],
    ])

    rows = EleveImportService.simulate(EleveImportService.read_xlsx(str(path)))

    assert [row.action for row in rows] == ["DOUBLON", "DOUBLON"]
