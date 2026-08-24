"""Tests cibles pour les correctifs apportes aux scripts d'import legacy :

- scripts/import_eleves.py : la date de naissance future est desormais rejetee,
  alignee sur la regle appliquee par EleveService.create_eleve.
- scripts/import_familles.py : un email invalide n'est plus supprime en silence,
  il est trace dans un rapport d'avertissements dedie.

Ces scripts n'ont pas besoin de la base de test (mode --analyze-only pour les
familles, fonctions pures pour les eleves) : pas de dependance a `db_session`.
"""
import sys
from datetime import date, timedelta

from openpyxl import Workbook

from scripts.import_eleves import as_date, _valid_birthdate
from scripts.import_familles import EXPECTED_HEADERS, main as import_familles_main
from scripts.import_inscriptions import (
    INSCRIPTION_HEADERS,
    NIVEAU_CLASSE_HEADERS,
    main as import_inscriptions_main,
)
from scripts.import_versements import (
    VERSEMENTCANT_HEADERS,
    VERSEMENTSCOL_HEADERS,
    main as import_versements_main,
)


# ─── import_eleves.py : date de naissance future rejetee ──────────────────────


def test_valid_birthdate_rejects_future_date():
    demain = date.today() + timedelta(days=1)
    assert _valid_birthdate(demain) is None


def test_valid_birthdate_accepts_today():
    assert _valid_birthdate(date.today()) == date.today()


def test_valid_birthdate_rejects_pre_1900():
    assert _valid_birthdate(date(1899, 12, 31)) is None


def test_as_date_string_format_rejects_future_date():
    futur = date.today() + timedelta(days=30)
    raw = futur.strftime("%d/%m/%Y")
    assert as_date(raw) is None


def test_as_date_string_format_accepts_past_date():
    assert as_date("01/01/2015") == date(2015, 1, 1)


# ─── import_familles.py : email invalide trace en avertissement ───────────────


def _build_minimal_familles_xlsx(path, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(EXPECTED_HEADERS)
    for row in rows:
        ws.append([row.get(h, "") for h in EXPECTED_HEADERS])
    wb.save(path)


def _run_import_familles(xlsx_path, rejects_path, warnings_path):
    old_argv = sys.argv
    sys.argv = [
        "import_familles.py", str(xlsx_path),
        "--analyze-only",
        "--rejects", str(rejects_path),
        "--warnings", str(warnings_path),
    ]
    try:
        return import_familles_main()
    finally:
        sys.argv = old_argv


def test_import_familles_reports_invalid_email_as_warning_not_silent_drop(tmp_path):
    xlsx_path = tmp_path / "familles.xlsx"
    warnings_path = tmp_path / "avertissements.csv"
    rejects_path = tmp_path / "rejets.csv"

    _build_minimal_familles_xlsx(xlsx_path, [{
        "IdTFamille": "1",
        "pa_nomResp": "Kouassi Jean",
        "pa_Qual": "1",
        "pa_Cel": "0700000000",
        "pa_Mail": "adresse-invalide-sans-arobase",
    }])

    rc = _run_import_familles(xlsx_path, rejects_path, warnings_path)

    assert rc == 0
    assert warnings_path.exists()
    content = warnings_path.read_text(encoding="utf-8-sig")
    assert "Email invalide" in content
    assert "adresse-invalide-sans-arobase" in content
    # La ligne reste importable malgre l'email invalide (pas un rejet).
    rejects_content = rejects_path.read_text(encoding="utf-8-sig")
    assert "Kouassi Jean" not in rejects_content


def test_import_familles_no_warning_when_email_valid(tmp_path):
    xlsx_path = tmp_path / "familles.xlsx"
    warnings_path = tmp_path / "avertissements.csv"
    rejects_path = tmp_path / "rejets.csv"

    _build_minimal_familles_xlsx(xlsx_path, [{
        "IdTFamille": "2",
        "pa_nomResp": "Yao Marie",
        "pa_Qual": "1",
        "pa_Cel": "0711111111",
        "pa_Mail": "marie.yao@example.com",
    }])

    rc = _run_import_familles(xlsx_path, rejects_path, warnings_path)

    assert rc == 0
    content = warnings_path.read_text(encoding="utf-8-sig")
    assert "Yao Marie" not in content


def _build_xlsx(path, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append([row.get(header, "") for header in headers])
    wb.save(path)


def _run_main(main, argv):
    old_argv = sys.argv
    sys.argv = argv
    try:
        return main()
    finally:
        sys.argv = old_argv


def test_import_inscriptions_analyze_only_needs_no_database(tmp_path, capsys):
    inscriptions = tmp_path / "inscriptions.xlsx"
    classes = tmp_path / "classes.xlsx"
    _build_xlsx(inscriptions, INSCRIPTION_HEADERS, [{"IDTInscription": 1, "IdClasse": 42}])
    _build_xlsx(classes, NIVEAU_CLASSE_HEADERS, [{
        "IDNiveau": 42, "Niv_Libelle": "CM2", "SINiveau": 0,
    }])

    rc = _run_main(import_inscriptions_main, [
        "import_inscriptions.py", str(inscriptions), str(classes),
        "--annee", "2026-2027", "--analyze-only",
    ])

    assert rc == 0
    assert "Inscriptions lues : 1" in capsys.readouterr().out


def test_import_versements_analyze_only_needs_no_database(tmp_path, capsys):
    scol = tmp_path / "versements_scol.xlsx"
    cant = tmp_path / "versements_cant.xlsx"
    _build_xlsx(scol, VERSEMENTSCOL_HEADERS, [{
        "IDVersementScol": 1, "DateVers": "01/09/2025",
    }])
    _build_xlsx(cant, VERSEMENTCANT_HEADERS, [{
        "IDVersementCant": 2, "DateVers": "date-invalide",
    }])

    rc = _run_main(import_versements_main, [
        "import_versements.py", str(scol), str(cant),
        "--annee", "2026-2027", "--analyze-only",
    ])

    assert rc == 0
    output = capsys.readouterr().out
    assert "Lignes lues : 2" in output
    assert "Dates absentes ou invalides : 1" in output
