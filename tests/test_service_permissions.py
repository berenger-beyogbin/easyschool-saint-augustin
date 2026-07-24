import datetime

import pytest

from app.session import AppSession
from services.comptabilite_service import ComptabiliteService
from services.profil_service import ProfilService
from services.utilisateur_service import UtilisateurService
from services.versement_service import VersementService


@pytest.mark.parametrize(
    "operation",
    [
        lambda: UtilisateurService.create({}),
        lambda: UtilisateurService.update(1, {}),
        lambda: UtilisateurService.toggle_active(1),
        lambda: UtilisateurService.delete(1),
        lambda: ProfilService.create({}),
        lambda: ProfilService.update(1, {}),
        lambda: ProfilService.delete(1),
        lambda: ProfilService.set_profil_permissions(1, set()),
        lambda: ComptabiliteService.create_mouvement("x", 1, datetime.date.today(), 1, "Debit"),
        lambda: ComptabiliteService.update_mouvement(1, "x", 1, datetime.date.today(), 1, "Debit"),
        lambda: ComptabiliteService.annuler_mouvement(1, "erreur"),
        lambda: VersementService.annuler_versement(1, "erreur"),
    ],
)
def test_sensitive_service_operations_require_permission(operation):
    AppSession.set_current_user({"Login": "sans-droit", "Nom": "Sans droit"}, set())

    ok, message = operation()

    assert ok is False
    assert message.startswith("Permission insuffisante pour ")


def test_create_versement_requires_permission():
    AppSession.set_current_user({"Login": "sans-droit", "Nom": "Sans droit"}, set())

    ok, message, new_id = VersementService.create_versement(
        1, 1, 1, datetime.date.today(), 1, 0, 0, 0
    )

    assert ok is False
    assert message == "Permission insuffisante pour enregistrer un versement."
    assert new_id is None
