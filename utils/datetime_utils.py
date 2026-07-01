from datetime import datetime, timezone


def utcnow() -> datetime:
    """Horodatage UTC naif, equivalent a l'ancien datetime.utcnow() (non deprecie)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
