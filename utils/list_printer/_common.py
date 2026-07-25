from PySide6.QtGui import QFont, QColor

C_BLACK      = QColor(0,   0,   0)
C_BORDER     = QColor(180, 180, 180)
C_HEADER_BG  = QColor(30,  41,  59)   # slate-800
C_ALT_ROW    = QColor(248, 250, 252)  # slate-50
C_NON_SOLDE  = QColor(220,  38,  38)  # red-600
C_SOLDE      = QColor(22,  163,  74)  # green-600
C_WARNING    = QColor(249, 115,  22)  # orange-600


def _font(size_pt: float, bold: bool = False) -> QFont:
    f = QFont("Arial", size_pt)
    f.setBold(bold)
    return f


def _fmt_f(montant) -> str:
    """Formate un montant en '150 000 F'."""
    try:
        val = int(float(montant))
        if val == 0:
            return "0 F"
        return f"{val:,}".replace(",", " ") + " F"
    except Exception:
        return "0 F"
