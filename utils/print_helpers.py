import os
from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import QMessageBox


@dataclass(frozen=True)
class EtablissementPrintInfo:
    type_etablissement: str
    nom: str
    telephone: str
    adresse: str
    logo_path: Optional[str]
    etablissement: object


def resolve_asset_path(path: Optional[str]) -> Optional[str]:
    """Retourne un chemin de fichier utilisable pour un asset configuré."""
    if not path:
        return None
    candidate = os.path.expanduser(path)
    if not os.path.isabs(candidate):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(project_root, candidate)
    candidate = os.path.normpath(candidate)
    return candidate if os.path.isfile(candidate) else None


def get_etablissement_print_info(parent=None) -> Optional[EtablissementPrintInfo]:
    """Charge l'identité d'impression ou avertit l'utilisateur et annule l'opération."""
    try:
        from services.etablissement_service import EtablissementService

        ecole = EtablissementService.get_etablissement()
        nom = (getattr(ecole, "RaisonSociale", "") or "").strip()
        if not nom:
            raise ValueError("le nom de l'établissement n'est pas renseigné")
        return EtablissementPrintInfo(
            type_etablissement=(getattr(ecole, "TypeEtab", "") or "").strip(),
            nom=nom,
            telephone=" / ".join(
                numero for numero in (
                    (getattr(ecole, "Telephone", "") or "").strip(),
                    (getattr(ecole, "TelephoneSecondaire", "") or "").strip(),
                ) if numero
            ),
            adresse=(getattr(ecole, "Adresse", "") or "").strip(),
            logo_path=resolve_asset_path(getattr(ecole, "LogoPath", None)),
            etablissement=ecole,
        )
    except Exception as exc:
        QMessageBox.critical(
            parent,
            "Impression impossible",
            "Les informations de l'établissement n'ont pas pu être chargées.\n"
            "Vérifiez Paramètres > Établissement, puis réessayez.\n\n"
            f"Détail : {exc}",
        )
        return None


def format_fcfa(montant) -> str:
    """Formate un montant sans décimales, avec le libellé monétaire officiel."""
    try:
        return f"{int(float(montant)):,}".replace(",", " ") + " FCFA"
    except (TypeError, ValueError, OverflowError):
        return "0 FCFA"


def payment_status_label(status) -> str:
    """Conserve les trois niveaux de paiement dans les états imprimés."""
    return {
        "Payé": "Soldé",
        "Partiel": "Partiel",
        "Impayé": "Impayé",
    }.get(str(status or "").strip(), "Impayé")
