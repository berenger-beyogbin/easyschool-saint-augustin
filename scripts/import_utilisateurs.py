"""Import sécurisé d'un ancien export GPWUTILISATEUR (.xls) dans Utilisateur.

Exemples :
  python scripts/import_utilisateurs.py "E:\\EXPORT EPC\\GPWUTILISATEUR.XLS" --analyze-only
  python scripts/import_utilisateurs.py "E:\\EXPORT EPC\\GPWUTILISATEUR.XLS"
  python scripts/import_utilisateurs.py "E:\\EXPORT EPC\\GPWUTILISATEUR.XLS" --commit

Sans --commit, la transaction est toujours annulée après simulation.

Mapping métier retenu avec l'utilisateur :
- Superviseur=1 (ancien flag) -> profil DIRECTEUR
- Superviseur=0 -> profil SECRETAIRE (à réassigner ensuite dans l'écran Utilisateurs)
- Login "SUPERVISEUR" (compte générique sans nom/prénom) -> ignoré, un compte admin existe déjà
- Ancien mot de passe en clair réutilisé (hashé), changement obligatoire à la 1re connexion
- Login déjà présent en base (insensible à la casse) -> ignoré
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import xlrd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_HEADERS = ["Login", "Nom", "Prenom", "MotPasse", "Superviseur"]
IGNORED_LOGIN = "SUPERVISEUR"


@dataclass
class Rejection:
    excel_row: int
    login: str
    reason: str


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def as_bool_flag(value: Any) -> bool:
    try:
        return float(value) == 1.0
    except (TypeError, ValueError):
        return False


def read_rows(path: Path) -> list[tuple[int, dict[str, Any]]]:
    workbook = xlrd.open_workbook(str(path))
    sheet = workbook.sheet_by_index(0)
    headers = [clean(sheet.cell_value(0, c)) for c in range(sheet.ncols)]
    missing = [h for h in EXPECTED_HEADERS if h not in headers]
    if missing:
        raise ValueError(f"Colonnes absentes de l'export : {', '.join(missing)}")
    rows = []
    for r in range(1, sheet.nrows):
        values = [sheet.cell_value(r, c) for c in range(sheet.ncols)]
        rows.append((r + 1, dict(zip(headers, values))))
    return rows


def write_rejections(path: Path, rows: list[Rejection]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["Ligne Excel", "Login", "Motif"])
        writer.writerows((r.excel_row, r.login, r.reason) for r in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Importer l'ancien export GPWUTILISATEUR vers Utilisateur.")
    parser.add_argument("xls", type=Path, help="Chemin du fichier GPWUTILISATEUR.XLS")
    parser.add_argument("--commit", action="store_true", help="Valider réellement l'import en base.")
    parser.add_argument("--analyze-only", action="store_true", help="Analyser le fichier sans connexion à la base.")
    parser.add_argument("--profil-superviseur", default="DIRECTEUR", help="Code profil pour Superviseur=1 (défaut : DIRECTEUR).")
    parser.add_argument("--profil-standard", default="SECRETAIRE", help="Code profil pour Superviseur=0 (défaut : SECRETAIRE).")
    parser.add_argument("--rejects", type=Path, default=Path("utilisateurs_rejetes.csv"))
    args = parser.parse_args()

    if not args.xls.is_file():
        parser.error(f"Fichier introuvable : {args.xls}")

    source_rows = read_rows(args.xls)

    if args.analyze_only:
        ignored = sum(1 for _, row in source_rows if clean(row.get("Login")).upper() == IGNORED_LOGIN)
        print(f"Lignes lues : {len(source_rows)}")
        print(f"Compte(s) générique(s) ignoré(s) ({IGNORED_LOGIN}) : {ignored}")
        for excel_row, row in source_rows:
            login = clean(row.get("Login"))
            superviseur = as_bool_flag(row.get("Superviseur"))
            print(f"  L{excel_row}: {login!r} Nom={clean(row.get('Nom'))!r} Prenom={clean(row.get('Prenom'))!r} Superviseur={superviseur}")
        return 0

    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    from app.database import get_session
    import models  # noqa: F401 - enregistre tous les mappers SQLAlchemy avant usage
    from models.utilisateur import Utilisateur
    from models.profil import Profil
    from services.utilisateur_service import _hash_password

    session = get_session()
    inserted = 0
    rejected: list[Rejection] = []
    try:
        profil_superviseur = session.query(Profil).filter_by(Code=args.profil_superviseur).first()
        profil_standard = session.query(Profil).filter_by(Code=args.profil_standard).first()
        if not profil_superviseur:
            print(f"Profil introuvable : {args.profil_superviseur}", file=sys.stderr)
            return 2
        if not profil_standard:
            print(f"Profil introuvable : {args.profil_standard}", file=sys.stderr)
            return 2

        existing_logins = {clean(login).casefold() for login in session.scalars(select(Utilisateur.Login))}

        for excel_row, row in source_rows:
            login = clean(row.get("Login"))
            nom = clean(row.get("Nom")) or login
            prenom = clean(row.get("Prenom"))
            password = clean(row.get("MotPasse"))
            superviseur = as_bool_flag(row.get("Superviseur"))

            if not login:
                rejected.append(Rejection(excel_row, login, "Login manquant"))
                continue
            if login.upper() == IGNORED_LOGIN:
                rejected.append(Rejection(excel_row, login, "Compte générique ignoré (décision utilisateur)"))
                continue
            if login.casefold() in existing_logins:
                rejected.append(Rejection(excel_row, login, "Login déjà présent dans la base"))
                continue
            if not password:
                rejected.append(Rejection(excel_row, login, "Mot de passe manquant"))
                continue

            user = Utilisateur(
                Login=login,
                MotDePasseHash=_hash_password(password),
                Nom=nom[:100],
                Prenoms=prenom[:150] or None,
                IDProfil=profil_superviseur.IDProfil if superviseur else profil_standard.IDProfil,
                IsActive=True,
                MustChangePassword=True,
            )
            session.add(user)
            existing_logins.add(login.casefold())
            inserted += 1

        session.flush()
        write_rejections(args.rejects, rejected)
        if args.commit:
            session.commit()
            action = "IMPORT VALIDÉ"
        else:
            session.rollback()
            action = "SIMULATION : aucune modification enregistrée"
        print(action)
        print(f"Lignes prêtes à être insérées : {inserted}")
        print(f"Lignes rejetées/ignorées : {len(rejected)}")
        print(f"Rapport : {args.rejects.resolve()}")
        return 0
    except IntegrityError as exc:
        session.rollback()
        print(f"Import annulé à cause d'une contrainte de base : {exc.orig}", file=sys.stderr)
        return 2
    except Exception as exc:
        session.rollback()
        print(f"Import annulé : {exc}", file=sys.stderr)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
