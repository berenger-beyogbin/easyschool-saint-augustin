import csv
import re
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import load_workbook
import models  # noqa: F401 -- enregistre toutes les relations SQLAlchemy
from app.database import get_session
from app.session import AppSession
from models.eleve import Eleve


REQUIRED_COLUMNS = {"CODE", "NOM ET PRENOMS", "DATE NAISSANCE", "SEXE"}


@dataclass
class EleveImportRow:
    excel_row: int
    code_externe: str
    matricule_national: str | None
    identite_originale: str
    nom: str
    prenoms: str
    date_naissance: date | None
    sexe: int | None
    deuxieme_langue: str | None
    statut_source: str | None
    redoublant_source: bool | None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    action: str = "A_CREER"
    matricule_interne: str | None = None

    @property
    def valide(self) -> bool:
        return not self.errors and self.action == "A_CREER"


class EleveImportService:
    @staticmethod
    def _open_workbook(path: str):
        """Ouvre un xlsx, y compris les exports contenant le typo `biltinId`.

        Certains anciens exports Excel ont cet attribut invalide dans styles.xml.
        La correction est faite uniquement dans une copie temporaire.
        """
        try:
            return load_workbook(path, read_only=True, data_only=True)
        except TypeError as exc:
            if "biltinId" not in str(exc):
                raise
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp:
            repaired_path = temp.name
        try:
            with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(repaired_path, "w") as target:
                for info in source.infolist():
                    content = source.read(info.filename)
                    if info.filename == "xl/styles.xml":
                        content = content.replace(b"biltinId", b"builtinId")
                    target.writestr(info, content)
            workbook = load_workbook(repaired_path, read_only=True, data_only=True)
            workbook._easy_school_temp_path = repaired_path
            return workbook
        except Exception:
            Path(repaired_path).unlink(missing_ok=True)
            raise

    @staticmethod
    def _text(value) -> str:
        return " ".join(str(value or "").strip().split())

    @staticmethod
    def _key(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        return " ".join("".join(c for c in normalized if not unicodedata.combining(c)).upper().split())

    @staticmethod
    def _date(value) -> date | None:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, (int, float)):
            return date(1899, 12, 30) + timedelta(days=int(value))
        text = str(value).strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _sexe(value) -> int | None:
        key = EleveImportService._key(str(value or ""))
        if key in {"M", "MASCULIN"}:
            return 1
        if key in {"F", "FEMININ"}:
            return 2
        return None

    @staticmethod
    def _lv2(value) -> str | None:
        key = EleveImportService._key(str(value or ""))
        if key in {"", "NULL", "-1"}:
            return None
        if key == "ESPAGNOL":
            return "ESPAGNOL"
        if key == "ALLEMAND":
            return "ALLEMAND"
        return EleveImportService._text(value).upper() or None

    @staticmethod
    def _redoublant(value) -> bool | None:
        key = EleveImportService._key(str(value or ""))
        if key in {"OUI", "R", "-1"}:
            return True
        if key == "NON":
            return False
        return None

    @staticmethod
    def _split_identity(value: str) -> tuple[str, str]:
        parts = EleveImportService._text(value).split(" ", 1)
        if len(parts) < 2:
            return (parts[0] if parts else ""), ""
        return parts[0], parts[1]

    @staticmethod
    def read_xlsx(path: str, sheet_name: str | None = None) -> list[EleveImportRow]:
        workbook = EleveImportService._open_workbook(path)
        try:
            sheet = workbook[sheet_name] if sheet_name else workbook.active
            iterator = sheet.iter_rows(values_only=True)
            headers = [EleveImportService._key(v) for v in next(iterator)]
            missing = REQUIRED_COLUMNS - set(headers)
            if missing:
                raise ValueError(f"Colonnes obligatoires absentes : {', '.join(sorted(missing))}")
            positions = {header: index for index, header in enumerate(headers)}
            result = []
            for excel_row, values in enumerate(iterator, start=2):
                if not any(value not in (None, "") for value in values):
                    continue
                def get(name):
                    return values[positions[name]] if name in positions and positions[name] < len(values) else None
                identity = EleveImportService._text(get("NOM ET PRENOMS")).upper()
                nom, prenoms = EleveImportService._split_identity(identity)
                birth_date = EleveImportService._date(get("DATE NAISSANCE"))
                sexe = EleveImportService._sexe(get("SEXE"))
                row = EleveImportRow(
                    excel_row=excel_row,
                    code_externe=EleveImportService._text(get("CODE")),
                    matricule_national=EleveImportService._text(get("MATRICULE")) or None,
                    identite_originale=identity,
                    nom=nom,
                    prenoms=prenoms,
                    date_naissance=birth_date,
                    sexe=sexe,
                    deuxieme_langue=EleveImportService._lv2(get("LV2")),
                    statut_source={"AFF": "AFFECTE_ETAT", "NAFF": "NON_AFFECTE_ETAT"}.get(
                        EleveImportService._key(str(get("STATUT") or ""))
                    ),
                    redoublant_source=EleveImportService._redoublant(get("REDOUBLE")),
                )
                if not row.code_externe:
                    row.errors.append("Code externe manquant")
                if not row.nom or not row.prenoms:
                    row.errors.append("Nom et prénoms impossibles à séparer")
                else:
                    row.warnings.append("Séparation automatique nom/prénoms à vérifier")
                if not birth_date:
                    row.errors.append("Date de naissance manquante ou invalide")
                elif birth_date > date.today():
                    row.errors.append("Date de naissance future")
                if sexe is None:
                    row.errors.append("Sexe manquant ou invalide")
                result.append(row)
            return result
        finally:
            workbook.close()
            temp_path = getattr(workbook, "_easy_school_temp_path", None)
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    @staticmethod
    def simulate(rows: list[EleveImportRow]) -> list[EleveImportRow]:
        session = get_session()
        try:
            existing_codes = {value for (value,) in session.query(Eleve.CodeExterne).filter(Eleve.CodeExterne.isnot(None))}
            existing_national = {
                EleveImportService._key(value) for (value,) in
                session.query(Eleve.MatriculeNational).filter(Eleve.MatriculeNational.isnot(None))
            }
            existing_identities = {
                (EleveImportService._key(nom), EleveImportService._key(prenoms), birth)
                for nom, prenoms, birth in session.query(Eleve.Nom, Eleve.Prenoms, Eleve.DateNaissance)
            }
            code_counts = {}
            national_counts = {}
            for row in rows:
                code_counts[row.code_externe] = code_counts.get(row.code_externe, 0) + 1
                if row.matricule_national:
                    key = EleveImportService._key(row.matricule_national)
                    national_counts[key] = national_counts.get(key, 0) + 1

            for row in rows:
                if row.errors:
                    row.action = "INVALIDE"
                    continue
                if row.code_externe in existing_codes:
                    row.action = "DEJA_IMPORTE"
                    continue
                if code_counts.get(row.code_externe, 0) > 1:
                    row.errors.append("Code externe en double dans le fichier")
                    row.action = "DOUBLON"
                    continue
                nat_key = EleveImportService._key(row.matricule_national or "")
                if nat_key and (nat_key in existing_national or national_counts.get(nat_key, 0) > 1):
                    row.errors.append("Matricule national en double")
                    row.action = "DOUBLON"
                    continue
                identity_key = (EleveImportService._key(row.nom), EleveImportService._key(row.prenoms), row.date_naissance)
                if identity_key in existing_identities:
                    row.errors.append("Identité et date déjà présentes")
                    row.action = "DOUBLON"
            return rows
        finally:
            session.close()

    @staticmethod
    def _matricule_prefix() -> str:
        libelle = AppSession.get_active_annee_libelle()
        if not libelle:
            raise ValueError("Aucune année scolaire active.")
        start = libelle.split("-")[0].strip()
        return start[-2:] if len(start) >= 2 else start.zfill(2)

    @staticmethod
    def import_rows(rows: list[EleveImportRow]) -> list[EleveImportRow]:
        candidates = [row for row in rows if row.valide]
        if not candidates:
            return rows
        prefix = EleveImportService._matricule_prefix()
        session = get_session()
        try:
            existing = session.query(Eleve.Matricule).filter(Eleve.Matricule.like(f"{prefix}-%")).all()
            maximum = 0
            for (matricule,) in existing:
                match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", matricule or "")
                if match:
                    maximum = max(maximum, int(match.group(1)))

            for offset, row in enumerate(candidates, start=1):
                row.matricule_interne = f"{prefix}-{maximum + offset:04d}"
                session.add(Eleve(
                    Matricule=row.matricule_interne,
                    CodeExterne=row.code_externe,
                    MatriculeNational=row.matricule_national,
                    Nom=row.nom[:35],
                    Prenoms=row.prenoms[:75],
                    DateNaissance=row.date_naissance,
                    Sexe=row.sexe,
                    DeuxiemeLangue=row.deuxieme_langue,
                    IDFamille=None,
                ))
            session.commit()
            for row in candidates:
                row.action = "CREE"
            return rows
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def export_report(rows: list[EleveImportRow], path: str) -> str:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow([
                "Ligne Excel", "Code externe", "Matricule national", "Identité originale",
                "Nom importé", "Prénoms importés", "Matricule interne", "Résultat", "Messages",
            ])
            for row in rows:
                writer.writerow([
                    row.excel_row, row.code_externe, row.matricule_national or "", row.identite_originale,
                    row.nom, row.prenoms, row.matricule_interne or "", row.action,
                    " | ".join(row.errors + row.warnings),
                ])
        return str(output)

    @staticmethod
    def summary(rows: list[EleveImportRow]) -> dict[str, int]:
        result = {"total": len(rows)}
        for row in rows:
            result[row.action] = result.get(row.action, 0) + 1
        return result
