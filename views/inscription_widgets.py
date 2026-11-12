"""Styles et petits constructeurs de widgets réutilisés par InscriptionView
(views/inscription_view.py).

Regroupés ici car indépendants de l'état de la vue : les deux fonctions ne
lisent ni n'écrivent aucun attribut ``self`` d'un InscriptionView, seulement
leurs paramètres.
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QCheckBox,
)
from PySide6.QtCore import Qt
from app.styles import COLORS, apply_card_shadow

_CARD_STYLE = """
QFrame#stepCard {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}
"""

_HEADER_STYLE = """
QFrame#cardHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EFF6FF, stop:1 #F8FAFC);
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid #DBEAFE;
}
"""

_BADGE_STYLE = """
QLabel {
    background-color: #2563EB;
    color: #FFFFFF;
    border-radius: 13px;
    font-size: 11px;
    font-weight: bold;
    border: none;
}
"""

_HEADER_TITLE_STYLE = (
    "font-size: 13px; font-weight: 700; color: #1D4ED8;"
    "background-color: transparent; border: none;"
)

_FIELD_LABEL_STYLE = (
    f"font-size: 10px; font-weight: 700; color: {COLORS['muted']};"
    "background-color: transparent; border: none; letter-spacing: 0.5px;"
)

_CHK_STYLE = f"""
QCheckBox {{
    color: {COLORS['text_soft']};
    font-size: 12px;
    font-weight: 500;
    background-color: transparent;
    spacing: 10px;
}}
QCheckBox:hover {{
    color: {COLORS['primary_dark']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['input_border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QCheckBox::indicator:unchecked:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QCheckBox::indicator:checked:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
"""

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
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:hover {{
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator {{
    width: 18px;
    height: 18px;
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

_BTN_INSCRIRE = f"""
QPushButton {{
    background-color: {COLORS['success']};
    color: #FFFFFF;
    padding: 0 20px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 9px;
    border: none;
    min-height: 50px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{ background-color: #15803D; }}
QPushButton:pressed {{ background-color: #166534; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

_BTN_MODIFIER = f"""
QPushButton {{
    background-color: {COLORS['warning']};
    color: #FFFFFF;
    padding: 0 20px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 9px;
    border: none;
    min-height: 50px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{ background-color: #EA6C00; }}
QPushButton:pressed {{ background-color: #C05500; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""


def make_step_card(step_num: str, title: str, scrollable: bool = False):
    """Crée une carte premium avec badge numéroté et header dégradé.

    Si scrollable=True, le corps de la carte est placé dans une QScrollArea :
    utile pour les cartes à contenu de longueur variable (ex. liste de frais
    annexes dépendant du niveau), qui ne doivent jamais être écrasées par la
    hauteur imposée par les cartes voisines dans la grille.
    """
    card = QFrame()
    card.setObjectName("stepCard")
    card.setStyleSheet(_CARD_STYLE)
    apply_card_shadow(card)

    card_vbox = QVBoxLayout(card)
    card_vbox.setContentsMargins(0, 0, 0, 0)
    card_vbox.setSpacing(0)

    header = QFrame()
    header.setObjectName("cardHeader")
    header.setStyleSheet(_HEADER_STYLE)
    header.setFixedHeight(46)
    hdr_layout = QHBoxLayout(header)
    hdr_layout.setContentsMargins(14, 0, 14, 0)
    hdr_layout.setSpacing(10)

    badge = QLabel(step_num)
    badge.setFixedSize(26, 26)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(_BADGE_STYLE)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(_HEADER_TITLE_STYLE)

    hdr_layout.addWidget(badge)
    hdr_layout.addWidget(lbl_title)
    hdr_layout.addStretch()
    card_vbox.addWidget(header)

    content = QFrame()
    content.setStyleSheet("QFrame { background-color: transparent; border: none; }")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(14, 12, 14, 14)
    content_layout.setSpacing(10)

    if scrollable:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        card_vbox.addWidget(scroll)
    else:
        card_vbox.addWidget(content)

    return card, content_layout


def make_option_row(checkbox: QCheckBox, wrap_text: str = None) -> QFrame:
    """Enveloppe un checkbox dans une ligne stylisée avec hover.

    Si wrap_text est fourni, le libellé est affiché via un QLabel à part
    (avec retour à la ligne automatique) plutôt que sur le texte natif du
    checkbox — un QCheckBox ne wrap jamais son texte, ce qui provoquait un
    débordement horizontal de la carte pour les libellés de frais longs.
    """
    frame = QFrame()
    frame.setObjectName("optionRow")
    frame.setStyleSheet("""
        QFrame#optionRow {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 7px;
        }
        QFrame#optionRow:hover {
            border-color: #93C5FD;
            background-color: #EFF6FF;
        }
    """)
    row = QHBoxLayout(frame)
    if wrap_text is not None:
        # Lignes de la liste des frais annexes : plus compactes pour
        # afficher davantage d'éléments avant de devoir défiler.
        row.setContentsMargins(10, 4, 10, 4)
        row.setSpacing(8)
    else:
        row.setContentsMargins(12, 7, 12, 7)
        row.setSpacing(10)
    row.addWidget(checkbox)
    if wrap_text is not None:
        checkbox.setText("")
        lbl = QLabel(wrap_text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 500; color: {COLORS['text_soft']};"
            "background-color: transparent; border: none;"
        )
        row.addWidget(lbl, 1)
    else:
        row.addStretch()
    return frame
