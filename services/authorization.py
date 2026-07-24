from app.session import AppSession


def permission_denied(code: str, action: str) -> tuple[bool, str] | None:
    """Retourne un refus prêt à renvoyer si la permission requise manque."""
    if AppSession.has_permission(code):
        return None
    return False, f"Permission insuffisante pour {action}."
