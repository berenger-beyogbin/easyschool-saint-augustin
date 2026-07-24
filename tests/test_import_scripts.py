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
