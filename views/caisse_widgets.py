"""Helpers et petits widgets réutilisés par CaisseView (views/caisse_view.py).

Regroupés ici car indépendants de l'état de la vue (aucune référence à
``self`` d'un CaisseView) : formatage de montants, style des chips/listes,
et le widget ToggleSwitch générique.
"""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from app.styles import COLORS, apply_card_shadow


def _compute_motif(m_scol: float, m_trans: float, m_cant: float, m_autres: float = 0) -> str:
    """Déduit un motif de paiement simple à partir des montants versés."""
    parts = []
    if m_scol > 0:
        parts.append("Scolarité")
    if m_trans > 0:
        parts.append("Transport")
    if m_cant > 0:
        parts.append("Cantine")
    if m_autres > 0:
        parts.append("Autres frais")
    return " + ".join(parts) if parts else "Scolarité"


# ─── Helpers montants ────────────────────────────────────────────────────────

def _fmt_input(v) -> str:
    """Formate un montant entier avec séparateur de milliers (espace)."""
    try:
        return f"{int(float(v)):,}".replace(",", " ")
    except Exception:
        return "0"


def _parse_input(text: str) -> float:
    """Parse un montant saisi (supporte les espaces comme séparateurs de milliers)."""
    return float(text.replace(" ", "").replace(",", "").strip() or 0)


# ─── Styles chip ─────────────────────────────────────────────────────────────

_CHIP_MUTED = (
    f"font-size: 11px; font-weight: 600; color: {COLORS['muted']};"
    f"background-color: {COLORS['border_soft']}; border: 1px solid {COLORS['border']};"
    "border-radius: 10px; padding: 3px 10px;"
)
_CHIP_SUCCESS = (
    f"font-size: 11px; font-weight: 600; color: {COLORS['success']};"
    "background-color: #DCFCE7; border: 1px solid #86EFAC;"
    "border-radius: 10px; padding: 3px 10px;"
)

_FRAIS_LIST_STYLE = f"""
QListWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    outline: none;
    font-size: 12px;
    color: {COLORS['text_soft']};
}}
QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:hover {{
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['input_border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QListWidget::indicator:unchecked:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QListWidget::indicator:checked:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
"""


# ─── Widget toggle ON/OFF ────────────────────────────────────────────────────

class ToggleSwitch(QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(64, 30)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
        self.toggled.connect(lambda _: self._apply_style())

    def _apply_style(self):
        if self.isChecked():
            self.setText("ON")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: #FFFFFF;
                    border-radius: 15px;
                    font-size: 10px;
                    font-weight: 800;
                    border: none;
                    letter-spacing: 1px;
                }
                QPushButton:hover { background-color: #15803D; }
            """)
        else:
            self.setText("OFF")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #CBD5E1;
                    color: #64748B;
                    border-radius: 15px;
                    font-size: 10px;
                    font-weight: 800;
                    border: none;
                    letter-spacing: 1px;
                }
                QPushButton:hover { background-color: #94A3B8; }
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._apply_style()


# ─── Helpers UI ──────────────────────────────────────────────────────────────

def _make_field_group(label_text: str, widget) -> QVBoxLayout:
    """Label uppercase + champ de saisie."""
    vbox = QVBoxLayout()
    vbox.setContentsMargins(0, 0, 0, 0)
    vbox.setSpacing(2)
    lbl = QLabel(label_text.upper())
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 700; color: #94A3B8;"
        "background-color: transparent; border: none; letter-spacing: 0.8px;"
    )
    # Le libellé ne doit jamais forcer le groupe à dépasser la largeur du champ
    # (ex. « AUTRES FRAIS » plus long que le QLineEdit de 130px) :
    # il se limite à cette largeur et passe à la ligne au besoin.
    field_width = widget.maximumWidth()
    if 0 < field_width < 16777215:
        lbl.setFixedWidth(field_width)
        lbl.setWordWrap(True)
    vbox.addWidget(lbl)
    vbox.addWidget(widget)
    return vbox


def _make_panel(accent_color: str) -> tuple:
    """Retourne (QFrame card, QVBoxLayout content) avec top-accent + ombre."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-top: 3px solid {accent_color};
            border-radius: 10px;
        }}
    """)
    apply_card_shadow(card)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)
    return card, layout
