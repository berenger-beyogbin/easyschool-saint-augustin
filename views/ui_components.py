"""Composants UI réutilisables pour Easy School 2.0 — v3."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QSizePolicy, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt

from app.styles import (
    COLORS,
    CARD_STYLE, SECTION_CARD_STYLE,
    SECTION_HEADER_STYLE, FORM_SECTION_STYLE, MODULE_HEADER_STYLE,
    BADGE_SUCCESS, BADGE_WARNING, BADGE_DANGER, BADGE_INFO,
    SECTION_LABEL_STYLE, INFO_LABEL_STYLE, MUTED_LABEL_STYLE,
    LABEL_STYLE, MESSAGEBOX_STYLE, INPUT_STYLE,
    apply_card_shadow, configure_button,
    configure_search_input,
)


# ---------------------------------------------------------------------------
# HELPERS POPUPS
# ---------------------------------------------------------------------------

def _make_box(parent, icon, title: str, message: str,
              buttons=QMessageBox.StandardButton.Ok) -> QMessageBox:
    """Crée un QMessageBox avec style appliqué."""
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(buttons)
    box.setStyleSheet(MESSAGEBOX_STYLE)
    return box


def show_info(parent, title: str, message: str) -> int:
    """Affiche une popup d'information."""
    box = _make_box(parent, QMessageBox.Icon.Information, title, message)
    return box.exec()


def show_warning(parent, title: str, message: str) -> int:
    """Affiche une popup d'avertissement."""
    box = _make_box(parent, QMessageBox.Icon.Warning, title, message)
    return box.exec()


def show_error(parent, title: str, message: str) -> int:
    """Affiche une popup d'erreur critique."""
    box = _make_box(parent, QMessageBox.Icon.Critical, title, message)
    return box.exec()


def show_success(parent, title: str, message: str) -> int:
    """Affiche une popup de succès."""
    box = _make_box(parent, QMessageBox.Icon.Information, title, message)
    return box.exec()


def show_confirm(parent, title: str, message: str) -> bool:
    """Affiche une popup de confirmation Oui/Non. Retourne True si Oui."""
    box = _make_box(
        parent,
        QMessageBox.Icon.Question,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    box.setDefaultButton(QMessageBox.StandardButton.No)
    return box.exec() == QMessageBox.StandardButton.Yes


# ---------------------------------------------------------------------------
# COMPOSANTS CARTES
# ---------------------------------------------------------------------------

class ModernCard(QFrame):
    """Carte blanche avec bordure et arrondi standardisés."""

    def __init__(self, parent=None, shadow=False):
        super().__init__(parent)
        self.setObjectName("modernCard")
        self.setStyleSheet(CARD_STYLE)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(10)
        if shadow:
            apply_card_shadow(self)

    def body_layout(self) -> QVBoxLayout:
        return self._layout


class SectionCard(QFrame):
    """Carte de section avec bordure et arrondi réduits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sectionCard")
        self.setStyleSheet(SECTION_CARD_STYLE)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)

    def body_layout(self) -> QVBoxLayout:
        return self._layout


class KpiCard(QFrame):
    """Carte KPI premium : icône accent + titre + valeur + barre de couleur."""

    def __init__(self, title: str, color: str = None, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        color = color or COLORS["primary"]
        self._color = color
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame#kpiCard:hover {{
                border-color: {color};
                background-color: #FAFCFF;
            }}
        """)
        apply_card_shadow(self)

        _hex = color.lstrip('#')
        _r, _g, _b = int(_hex[0:2], 16), int(_hex[2:4], 16), int(_hex[4:6], 16)
        icon_bg = f"rgba({_r},{_g},{_b},0.12)"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 14)
        main_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #64748B;"
            "background-color: transparent; border: none;"
        )
        self.lbl_title.setWordWrap(True)
        top_row.addWidget(self.lbl_title, 1)

        if icon:
            icon_pill = QFrame()
            icon_pill.setFixedSize(48, 48)
            icon_pill.setStyleSheet(f"""
                QFrame {{
                    background-color: {icon_bg};
                    border-radius: 12px;
                    border: none;
                }}
            """)
            pill_layout = QHBoxLayout(icon_pill)
            pill_layout.setContentsMargins(0, 0, 0, 0)
            pill_layout.setSpacing(0)
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet(
                f"font-size: 24px; color: {color}; background-color: transparent; border: none;"
            )
            lbl_icon.setAlignment(Qt.AlignCenter)
            pill_layout.addWidget(lbl_icon)
            top_row.addWidget(icon_pill)

        main_layout.addLayout(top_row)

        self.lbl_value = QLabel("—")
        self.lbl_value.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        self.lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        main_layout.addWidget(self.lbl_value)

        accent_bar = QFrame()
        accent_bar.setFixedHeight(3)
        accent_bar.setStyleSheet(
            f"background-color: {color}; border: none; border-radius: 1px;"
        )
        main_layout.addWidget(accent_bar)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


class SectionHeader(QFrame):
    """En-tête de section : titre à gauche, boutons optionnels à droite."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("sectionHeader")
        self.setStyleSheet(SECTION_HEADER_STYLE)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 11, 16, 11)
        layout.setSpacing(10)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)

        lbl = QLabel(title)
        lbl.setStyleSheet(SECTION_LABEL_STYLE)
        text_block.addWidget(lbl)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet(INFO_LABEL_STYLE)
            text_block.addWidget(lbl_sub)

        layout.addLayout(text_block)
        layout.addStretch()

        self._btn_area = QHBoxLayout()
        self._btn_area.setSpacing(8)
        layout.addLayout(self._btn_area)

    def add_button(self, label: str, style: str = None, callback=None) -> QPushButton:
        btn = QPushButton(label)
        if style:
            btn.setStyleSheet(style)
        else:
            configure_button(btn, variant="primary")
        if callback:
            btn.clicked.connect(callback)
        self._btn_area.addWidget(btn)
        return btn


class EmptyState(QWidget):
    """Widget état vide centré — aucune donnée."""

    def __init__(self, icon: str = "○", title: str = "Aucune donnée",
                 message: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                f"font-size: 32px; color: {COLORS['border']}; background-color: transparent;"
            )
            layout.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['muted']};"
            "background-color: transparent;"
        )
        layout.addWidget(lbl_title)

        if message:
            lbl_msg = QLabel(message)
            lbl_msg.setAlignment(Qt.AlignCenter)
            lbl_msg.setWordWrap(True)
            lbl_msg.setStyleSheet(
                f"font-size: 12px; color: {COLORS['muted']}; background-color: transparent;"
            )
            layout.addWidget(lbl_msg)


class StatusBadge(QLabel):
    """Badge de statut coloré : success, warning, danger, info."""

    STATUS_STYLES = {
        "success": BADGE_SUCCESS,
        "warning": BADGE_WARNING,
        "danger":  BADGE_DANGER,
        "info":    BADGE_INFO,
    }

    def __init__(self, text: str, status: str = "info", parent=None):
        super().__init__(text, parent)
        style = self.STATUS_STYLES.get(status, BADGE_INFO)
        self.setStyleSheet(style)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(22)


class FinancialRow(QFrame):
    """Ligne financière : libellé à gauche, montant à droite, accent couleur optionnel."""

    def __init__(self, label: str, value: str = "0 FCFA", color: str = None,
                 bold: bool = False, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        weight = "bold" if bold else "500"
        size = "13px" if bold else "12px"
        label_color = COLORS['text_soft'] if not bold else COLORS['text']
        value_color = color or COLORS['text']

        self.lbl_label = QLabel(label)
        self.lbl_label.setStyleSheet(
            f"font-size: {size}; font-weight: {weight}; color: {label_color};"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(self.lbl_label, 1)

        self.lbl_value = QLabel(value)
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(
            f"font-size: {size}; font-weight: {weight}; color: {value_color};"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str):
        self.lbl_value.setText(value)

    def set_color(self, color: str):
        current = self.lbl_value.styleSheet()
        import re
        new = re.sub(r"color: [^;]+;", f"color: {color};", current, count=1)
        self.lbl_value.setStyleSheet(new)


class QuickActionButton(QPushButton):
    """Bouton d'accès rapide avec style secondaire standardisé."""

    def __init__(self, label: str, parent=None):
        super().__init__(label, parent)
        configure_button(self, variant="secondary", fixed_height=32, min_width=90)


class FinancialSection(QFrame):
    """Panneau section financière : titre + séparateur + lignes."""

    def __init__(self, title: str, accent_color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("financialSection")
        self._color = accent_color or COLORS['primary']
        self.setStyleSheet(f"""
            QFrame#financialSection {{
                background-color: {COLORS['surface_soft']};
                border: 1px solid {COLORS['border']};
                border-left: 3px solid {self._color};
                border-radius: 6px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {self._color};"
            "background-color: transparent; border: none; letter-spacing: 0.3px;"
        )
        self._layout.addWidget(lbl_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"color: {COLORS['border']}; background-color: {COLORS['border']}; border: none;"
        )
        sep.setFixedHeight(1)
        self._layout.addWidget(sep)

        self._rows = QVBoxLayout()
        self._rows.setSpacing(3)
        self._layout.addLayout(self._rows)

    def add_row(self, label: str, value: str = "0 FCFA", color: str = None,
                bold: bool = False) -> "FinancialRow":
        row = FinancialRow(label, value, color, bold)
        self._rows.addWidget(row)
        return row


# ---------------------------------------------------------------------------
# NOUVEAUX COMPOSANTS
# ---------------------------------------------------------------------------

class FormSection(QFrame):
    """Section de formulaire avec titre et layout vertical."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("formSection")
        self.setStyleSheet(FORM_SECTION_STYLE)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setStyleSheet(SECTION_LABEL_STYLE)
            self._layout.addWidget(lbl)

    def body_layout(self) -> QVBoxLayout:
        return self._layout


class SearchToolbar(QFrame):
    """Barre de recherche avec champ et boutons optionnels."""

    def __init__(self, placeholder: str = "Rechercher...", parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setStyleSheet(INPUT_STYLE)
        configure_search_input(self.search_input)
        layout.addWidget(self.search_input)

        self._btn_area = QHBoxLayout()
        self._btn_area.setSpacing(6)
        layout.addLayout(self._btn_area)

    def add_button(self, label: str, variant: str = "secondary",
                   callback=None) -> QPushButton:
        btn = QPushButton(label)
        configure_button(btn, variant=variant)
        if callback:
            btn.clicked.connect(callback)
        self._btn_area.addWidget(btn)
        return btn


class ActionBar(QFrame):
    """Barre d'actions horizontale, boutons alignés à droite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch()

    def add_button(self, label: str, variant: str = "primary",
                   callback=None) -> QPushButton:
        btn = QPushButton(label)
        configure_button(btn, variant=variant)
        if callback:
            btn.clicked.connect(callback)
        self._layout.addWidget(btn)
        return btn


class FinancialStatusCard(QFrame):
    """Carte de statut financier avec indicateur coloré."""

    def __init__(self, title: str, value: str = "0 FCFA",
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        color = color or COLORS["primary"]
        self.setStyleSheet(f"""
            QFrame#kpiCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(MUTED_LABEL_STYLE)
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color};"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


# ---------------------------------------------------------------------------
# HELPERS LABELS
# ---------------------------------------------------------------------------

def make_plain_label(text: str) -> QLabel:
    """Crée un QLabel simple sans bordure."""
    lbl = QLabel(text)
    lbl.setStyleSheet(LABEL_STYLE)
    return lbl


def make_section_title_label(text: str) -> QLabel:
    """Crée un QLabel titre de section."""
    lbl = QLabel(text)
    lbl.setStyleSheet(SECTION_LABEL_STYLE)
    return lbl


# ---------------------------------------------------------------------------
# FONCTIONS FACTORY
# ---------------------------------------------------------------------------

def make_module_header(title: str, subtitle: str = "") -> QFrame:
    """Crée un en-tête de module propre avec titre et sous-titre."""
    frame = QFrame()
    frame.setObjectName("module_header")
    frame.setStyleSheet(MODULE_HEADER_STYLE)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 14, 22, 14)
    layout.setSpacing(3)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(
        f"font-size: 16px; font-weight: bold; color: {COLORS['primary_dark']};"
        "background-color: transparent; border: none;"
    )
    layout.addWidget(lbl_title)

    if subtitle:
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet(INFO_LABEL_STYLE)
        layout.addWidget(lbl_sub)

    return frame


def make_separator(color: str = None) -> QFrame:
    """Crée un séparateur horizontal discret."""
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    c = color or COLORS['border']
    sep.setStyleSheet(f"color: {c}; background-color: {c}; border: none;")
    sep.setFixedHeight(1)
    return sep
