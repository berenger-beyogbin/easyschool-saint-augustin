from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel, QWidget

from ._colors import COLORS
from ._tables import TABLE_STYLE, TABLE_STYLE_YELLOW
from ._typography import PAGE_TITLE_STYLE, SECTION_TITLE_STYLE, PLACEHOLDER_STYLE, FIELD_LABEL_STYLE
from ._buttons import (
    BUTTON_PRIMARY, BUTTON_SUCCESS, BUTTON_SECONDARY, BUTTON_DANGER, BUTTON_WARNING,
    BUTTON_PRINT, BUTTON_TABLE_ACTION, BUTTON_TABLE_ACTION_PRIMARY,
    BUTTON_TABLE_ACTION_DANGER, BUTTON_TABLE_ACTION_WARNING,
)
from ._dialogs import MESSAGEBOX_STYLE

# ---------------------------------------------------------------------------
# FONCTIONS HELPERS
# ---------------------------------------------------------------------------

def apply_table_style(table, alternate="blue"):
    """Applique le style moderne au QTableWidget."""
    if alternate == "yellow":
        table.setStyleSheet(TABLE_STYLE_YELLOW)
    else:
        table.setStyleSheet(TABLE_STYLE)
    table.setAlternatingRowColors(True)
    from PySide6.QtWidgets import QAbstractItemView
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setHighlightSections(False)


def apply_financial_table_style(table):
    """Style spécifique pour les tableaux financiers (montants à droite)."""
    apply_table_style(table)
    table.setStyleSheet(TABLE_STYLE + """
    QTableWidget::item[financial="true"] {
        text-align: right;
    }
    """)


def apply_form_section_style(widget):
    """Applique le style section card à un widget."""
    widget.setStyleSheet(f"""
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
    """)


def apply_modal_style(dialog):
    """Applique le style modal à un QDialog."""
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['bg']};
        }}
        QGroupBox {{
            font-weight: bold;
            font-size: 13px;
            color: {COLORS['text_soft']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            margin-top: 14px;
            background-color: {COLORS['card']};
            padding-top: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 6px;
            color: {COLORS['text_soft']};
            background-color: {COLORS['card']};
        }}
        QLineEdit {{
            padding: 5px 8px;
            border: 1px solid {COLORS['input_border']};
            border-radius: 5px;
            background-color: {COLORS['card']};
            color: {COLORS['text']};
            min-height: 30px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1.5px solid {COLORS['primary']};
        }}
        QComboBox {{
            padding: 5px 8px;
            border: 1px solid {COLORS['input_border']};
            border-radius: 5px;
            background-color: {COLORS['card']};
            color: {COLORS['text']};
            min-height: 30px;
            font-size: 13px;
        }}
        QLabel {{
            color: {COLORS['text_soft']};
            font-size: 13px;
            background-color: transparent;
            border: none;
        }}
        QCheckBox {{
            color: {COLORS['text_soft']};
            font-size: 13px;
        }}
        QPushButton {{
            background-color: {COLORS['surface_soft']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['input_border']};
            border-radius: 7px;
            padding: 5px 18px;
            min-width: 80px;
            min-height: 30px;
            font-size: 14px;
            font-weight: 600;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {COLORS['border']};
            color: {COLORS['text']};
        }}
        QPushButton:pressed {{
            background-color: #D1D5DB;
            color: {COLORS['text']};
        }}
        QPushButton:default {{
            background-color: {COLORS['primary']};
            color: #FFFFFF;
            border-color: {COLORS['primary']};
        }}
        QPushButton:default:hover {{
            background-color: {COLORS['primary_dark']};
            color: #FFFFFF;
        }}
        QPushButton:default:pressed {{
            background-color: #1E3A8A;
            color: #FFFFFF;
        }}
    """)


def install_messagebox_autostyle():
    """Force TOUTE QMessageBox (y compris via QMessageBox.warning/information/
    critical/question) à recevoir explicitement MESSAGEBOX_STYLE sur l'instance.

    Nécessaire car le style applicatif global (QApplication.setStyleSheet) est
    "masqué" pour une QMessageBox dès que son widget parent a lui-même un
    setStyleSheet local (cas de quasi toutes les vues de l'app) : Qt fait alors
    remonter la cascade jusqu'à l'ancêtre le plus proche possédant un style,
    sans redescendre vers le style de l'application pour les propriétés
    manquantes — le bouton par défaut retombe sur le rendu Fusion natif
    (texte "BrightText" blanc sur fond quasi blanc = illisible).
    À appeler une seule fois, tôt dans main().
    """
    from PySide6.QtWidgets import QMessageBox

    _ICONS = {
        "warning": QMessageBox.Icon.Warning,
        "information": QMessageBox.Icon.Information,
        "critical": QMessageBox.Icon.Critical,
        "question": QMessageBox.Icon.Question,
    }

    def _make(kind):
        icon = _ICONS[kind]

        def _fn(parent, title, text,
                buttons=QMessageBox.StandardButton.NoButton,
                defaultButton=QMessageBox.StandardButton.NoButton):
            box = QMessageBox(parent)
            box.setIcon(icon)
            box.setWindowTitle(title)
            box.setText(text)
            if buttons != QMessageBox.StandardButton.NoButton:
                box.setStandardButtons(buttons)
            elif kind == "question":
                box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
            else:
                box.setStandardButtons(QMessageBox.StandardButton.Ok)
            if defaultButton != QMessageBox.StandardButton.NoButton:
                box.setDefaultButton(defaultButton)
            box.setStyleSheet(MESSAGEBOX_STYLE)
            return box.exec()

        return _fn

    QMessageBox.warning = staticmethod(_make("warning"))
    QMessageBox.information = staticmethod(_make("information"))
    QMessageBox.critical = staticmethod(_make("critical"))
    QMessageBox.question = staticmethod(_make("question"))


def apply_card_shadow(widget):
    """Applique une ombre légère via QGraphicsDropShadowEffect."""
    try:
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 25))
        widget.setGraphicsEffect(shadow)
    except Exception:
        pass


def make_title_label(text: str):
    """Crée un QLabel titre de page."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet(PAGE_TITLE_STYLE)
    return lbl


def make_section_label(text: str):
    """Crée un QLabel titre de section."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet(SECTION_TITLE_STYLE)
    return lbl


def make_section_title(text: str):
    """Alias de make_section_label pour compatibilité."""
    return make_section_label(text)


def make_placeholder_message(text: str):
    """Crée un QLabel de placeholder centré."""
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
    lbl = QLabel(text)
    lbl.setStyleSheet(PLACEHOLDER_STYLE)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    return lbl


def format_fcfa(montant) -> str:
    """Formate un montant en FCFA avec séparateurs de milliers."""
    try:
        val = int(float(montant))
        return f"{val:,} FCFA".replace(",", " ")
    except (ValueError, TypeError):
        return "0 FCFA"


# ---------------------------------------------------------------------------
# HELPERS BOUTONS
# ---------------------------------------------------------------------------

def configure_button(button, variant: str = "primary", fixed_height: int = 34,
                     min_width=None) -> None:
    """Configure un bouton avec un style standardisé (primary/success/secondary/danger/warning/print)."""
    from PySide6.QtWidgets import QSizePolicy
    from PySide6.QtCore import Qt
    styles = {
        "primary":   BUTTON_PRIMARY,
        "success":   BUTTON_SUCCESS,
        "secondary": BUTTON_SECONDARY,
        "danger":    BUTTON_DANGER,
        "warning":   BUTTON_WARNING,
        "print":     BUTTON_PRINT,
    }
    button.setStyleSheet(styles.get(variant, BUTTON_PRIMARY))
    button.setFixedHeight(fixed_height)
    if min_width is not None:
        button.setMinimumWidth(min_width)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


def configure_table_action_button(button, variant: str = "danger") -> None:
    """Configure un bouton pour utilisation dans une cellule de tableau."""
    from PySide6.QtWidgets import QSizePolicy
    from PySide6.QtCore import Qt
    styles = {
        "primary": BUTTON_TABLE_ACTION_PRIMARY,
        "danger":  BUTTON_TABLE_ACTION_DANGER,
        "warning": BUTTON_TABLE_ACTION_WARNING,
        "neutral": BUTTON_TABLE_ACTION,
    }
    button.setStyleSheet(styles.get(variant, BUTTON_TABLE_ACTION_DANGER))
    button.setFixedHeight(32)
    button.setMinimumWidth(95)
    button.setMaximumWidth(130)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


def make_field_label(text: str) -> "QLabel":
    """Crée un QLabel compact pour étiqueter un champ, sans bordure."""
    from PySide6.QtWidgets import QLabel
    lbl = QLabel(text)
    lbl.setStyleSheet(FIELD_LABEL_STYLE)
    return lbl


def configure_compact_input(widget, width: int = 165, height: int = 36) -> "QWidget":
    """Contraint un champ de saisie à une largeur et hauteur fixes compactes."""
    from PySide6.QtWidgets import QSizePolicy
    widget.setFixedWidth(width)
    widget.setFixedHeight(height)
    widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return widget


def configure_search_input(widget, max_width: int = 650, height: int = 36) -> "QWidget":
    """Contraint un champ de recherche à une largeur maximale."""
    from PySide6.QtWidgets import QSizePolicy
    widget.setMaximumWidth(max_width)
    widget.setFixedHeight(height)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return widget


def make_stat_card(title: str, color: str):
    """Crée une carte métrique (titre petit + valeur grande colorée).
    Retourne (card_widget, value_label)."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    card = QWidget()
    card.setObjectName("stat_card")
    card.setStyleSheet(f"""
        QWidget#stat_card {{
            background-color: #FFFFFF;
            border-left: 3px solid {color};
            border-radius: 5px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 6, 14, 6)
    layout.setSpacing(1)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        "font-size: 11px; color: #64748B; background: transparent; border: none;"
    )
    lbl_value = QLabel("—")
    lbl_value.setStyleSheet(
        f"font-size: 16px; font-weight: bold; color: {color}; background: transparent; border: none;"
    )
    layout.addWidget(lbl_title)
    layout.addWidget(lbl_value)
    return card, lbl_value


def make_totaux_panel_widget(cards_config: list):
    """Crée un panneau de totaux avec cartes métriques colorées.
    cards_config: liste de (title, color)
    Retourne (panel_widget, [lbl_value1, lbl_value2, ...])"""
    from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame
    panel = QWidget()
    panel.setObjectName("totaux_outer")
    panel.setStyleSheet(f"""
        QWidget#totaux_outer {{
            background-color: {COLORS['primary_soft']};
            border: 1px solid {COLORS['accent_blue']};
            border-radius: 8px;
        }}
    """)
    layout = QHBoxLayout(panel)
    layout.setContentsMargins(10, 6, 10, 6)
    layout.setSpacing(8)
    value_labels = []
    for i, (title, color) in enumerate(cards_config):
        if i > 0:
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']}; border: none; max-width: 1px;")
            layout.addWidget(sep)
        card, lbl_val = make_stat_card(title, color)
        layout.addWidget(card)
        value_labels.append(lbl_val)
    layout.addStretch()
    return panel, value_labels


def make_table_action_container(button) -> "QWidget":
    """Enveloppe un bouton dans un conteneur centré pour setCellWidget."""
    from PySide6.QtWidgets import QWidget, QHBoxLayout
    container = QWidget()
    container.setStyleSheet("background-color: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 3, 4, 3)
    layout.setSpacing(0)
    layout.addStretch(1)
    layout.addWidget(button)
    layout.addStretch(1)
    return container
