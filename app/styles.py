# Design system Easy School 2.0 — Amélioration IHM Nette v3
# Toutes les constantes et helpers visuels centralisés ici.

import pathlib
_ASSETS = str(pathlib.Path(__file__).parent.parent / "assets").replace("\\", "/")

# ---------------------------------------------------------------------------
# PALETTE DE COULEURS
# ---------------------------------------------------------------------------

COLORS = {
    "sidebar_bg":       "#0F172A",   # slate-900
    "sidebar_bg_2":     "#1E293B",   # slate-800
    "primary":          "#2563EB",   # blue-600
    "primary_dark":     "#1D4ED8",   # blue-700
    "primary_soft":     "#EFF6FF",   # blue-50
    "success":          "#16A34A",
    "danger":           "#DC2626",
    "warning":          "#F97316",
    "purple":           "#7C3AED",
    "bg":               "#F8FAFC",
    "surface":          "#FFFFFF",
    "surface_soft":     "#EFF6FF",   # blue-50
    "card":             "#FFFFFF",
    "text":             "#0F172A",   # slate-900
    "text_soft":        "#1E293B",   # slate-800
    "muted":            "#334155",   # slate-700
    "border":           "#E2E8F0",
    "border_soft":      "#F1F5F9",
    "input_border":     "#CBD5E1",
    "table_header":     "#F1F5F9",
    "table_row_alt":    "#F8FAFC",
    "table_selected":   "#DBEAFE",   # blue-100
    "table_alt_blue":   "#EFF6FF",   # blue-50
    "table_alt_yellow": "#FEF9C3",
    "selection":        "#DBEAFE",   # blue-100
    "hover":            "#EFF6FF",   # blue-50
    "accent_blue":      "#DBEAFE",   # blue-100
    "accent_green":     "#DCFCE7",
    "accent_orange":    "#FFF7ED",
    "accent_red":       "#FEF2F2",
    "accent_purple":    "#F5F3FF",
}

# ---------------------------------------------------------------------------
# ALIASES COULEURS (compatibilité vues existantes)
# ---------------------------------------------------------------------------
COLOR_PRIMARY_BLUE  = "#2563EB"          # bleu vrai
COLOR_LIGHT_BLUE    = "#DBEAFE"          # bleu-100 clair
COLOR_WHITE         = COLORS["card"]
COLOR_TEXT_MAIN     = COLORS["text"]
COLOR_TEXT_MUTED    = COLORS["muted"]
COLOR_BORDER        = COLORS["border"]
COLOR_DANGER        = COLORS["danger"]

# ---------------------------------------------------------------------------
# APP STYLE GLOBAL
# ---------------------------------------------------------------------------
APP_STYLE = f"""
QWidget {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: {COLORS['text']};
    background-color: {COLORS['bg']};
}}
QScrollBar:vertical {{
    border: none;
    background: #F1F5F9;
    width: 7px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    border: none;
    background: #F1F5F9;
    height: 7px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: #CBD5E1;
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{ background: #94A3B8; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QCheckBox {{
    color: {COLORS['text']};
    background-color: transparent;
    spacing: 8px;
    font-size: 14px;
}}
QCheckBox:disabled {{
    color: #9CA3AF;
}}
QToolTip {{
    background-color: {COLORS['text']};
    color: #FFFFFF;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 13px;
}}
"""

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
SIDEBAR_STYLE = f"""
QFrame#sidebar {{
    background-color: {COLORS['sidebar_bg']};
    min-width: 235px;
    max-width: 235px;
}}
"""

SIDEBAR_MENU_STYLE = """
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}
QListWidget::item {
    margin: 2px 0;
}
"""

# ---------------------------------------------------------------------------
# TOPBAR
# ---------------------------------------------------------------------------
TOPBAR_STYLE = f"""
QFrame#topbar {{
    background-color: {COLORS['card']};
    border-bottom: 1px solid {COLORS['border']};
    min-height: 56px;
    max-height: 56px;
}}
"""

# ---------------------------------------------------------------------------
# CONTENEUR DE PAGE
# ---------------------------------------------------------------------------
PAGE_CONTAINER_STYLE = f"background-color: {COLORS['bg']};"

# ---------------------------------------------------------------------------
# TITRES ET SECTIONS
# ---------------------------------------------------------------------------
PAGE_TITLE_STYLE = (
    f"font-size: 19px; font-weight: bold; color: {COLORS['primary_dark']};"
    "background-color: transparent; border: none; letter-spacing: 0.2px;"
)

PAGE_SUBTITLE_STYLE = (
    f"font-size: 13px; color: {COLORS['muted']}; background-color: transparent; border: none;"
)

SECTION_TITLE_STYLE = (
    f"font-size: 14px; font-weight: bold; color: {COLORS['primary_dark']};"
    "background-color: transparent; border: none;"
)

MODULE_HEADER_STYLE = f"""
QFrame#module_header {{
    background-color: {COLORS['card']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 0;
}}
"""

# ---------------------------------------------------------------------------
# ÉTIQUETTES (background: transparent; border: none obligatoires)
# ---------------------------------------------------------------------------
LABEL_STYLE = (
    f"font-size: 14px; color: {COLORS['text']}; background-color: transparent; border: none;"
)

STYLE_LABEL_TITLE = (
    f"font-size: 16px; font-weight: bold; color: {COLORS['primary_dark']};"
    "background-color: transparent; border: none;"
)
STYLE_LABEL_SUBTITLE = (
    f"font-size: 13px; font-weight: bold; color: {COLORS['text_soft']};"
    "background-color: transparent; border: none;"
)
STYLE_LABEL = (
    f"font-size: 13px; font-weight: 500; color: {COLORS['text_soft']};"
    "background-color: transparent; border: none;"
)

PANEL_TITLE_STYLE = (
    f"font-size: 14px; font-weight: bold; color: {COLORS['text_soft']};"
    "background-color: transparent; border: none;"
)

FIELD_LABEL_STYLE = (
    f"font-size: 12px; font-weight: 600; color: {COLORS['muted']};"
    "background-color: transparent; border: none;"
)

SECTION_LABEL_STYLE = (
    f"font-size: 14px; font-weight: bold; color: {COLORS['primary_dark']};"
    "background-color: transparent; border: none;"
)

INFO_LABEL_STYLE = (
    f"font-size: 13px; color: {COLORS['muted']}; background-color: transparent; border: none;"
)

MUTED_LABEL_STYLE = (
    f"font-size: 13px; color: {COLORS['muted']}; background-color: transparent; border: none;"
)

VALUE_LABEL_STYLE = (
    f"font-size: 14px; font-weight: 600; color: {COLORS['text']};"
    "background-color: transparent; border: none;"
)

# ---------------------------------------------------------------------------
# CARTES (ciblées par objectName pour éviter la cascade générique)
# ---------------------------------------------------------------------------
CARD_STYLE = f"""
QFrame#modernCard {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
"""

SECTION_CARD_STYLE = f"""
QFrame#sectionCard {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
"""

KPI_CARD_STYLE = f"""
QFrame#kpiCard {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QFrame#kpiCard:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
"""

SECTION_HEADER_STYLE = f"""
QFrame#sectionHeader {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
"""

FINANCIAL_SECTION_STYLE = f"""
QFrame#financialSection {{
    background-color: {COLORS['surface_soft']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
"""

FORM_SECTION_STYLE = f"""
QFrame#formSection {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
"""

PANEL_CARD_STYLE = f"""
QFrame#panelCard {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
"""

# ---------------------------------------------------------------------------
# CHAMPS DE SAISIE
# ---------------------------------------------------------------------------
INPUT_STYLE = f"""
QLineEdit {{
    padding: 6px 10px;
    border: 1px solid {COLORS['input_border']};
    border-radius: 6px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    min-height: 34px;
    font-size: 14px;
}}
QLineEdit:focus {{
    border: 1.5px solid {COLORS['primary']};
    background-color: #FAFCFF;
}}
QLineEdit:disabled {{
    background-color: {COLORS['surface_soft']};
    color: #9CA3AF;
    border-color: {COLORS['border']};
}}
QLineEdit::placeholder {{
    color: #64748B;
}}
"""
STYLE_LINEEDIT = INPUT_STYLE

COMBO_STYLE = f"""
QComboBox {{
    padding: 6px 10px;
    border: 1px solid {COLORS['input_border']};
    border-radius: 6px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    min-height: 34px;
    font-size: 14px;
}}
QComboBox:focus {{
    border: 1.5px solid {COLORS['primary']};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {COLORS['input_border']};
    border-radius: 0 6px 6px 0;
    background-color: {COLORS['surface_soft']};
}}
QComboBox::down-arrow {{
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_soft']};
    width: 0;
    height: 0;
}}
QComboBox::down-arrow:on {{
    border-top: none;
    border-bottom: 6px solid {COLORS['text_soft']};
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['selection']};
    selection-color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 2px;
}}
QComboBox:disabled {{
    background-color: {COLORS['surface_soft']};
    color: #9CA3AF;
}}
"""
STYLE_COMBOBOX = COMBO_STYLE

DATE_STYLE = f"""
QDateEdit {{
    padding: 6px 10px;
    border: 1px solid {COLORS['input_border']};
    border-radius: 6px;
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    min-height: 34px;
    font-size: 14px;
}}
QDateEdit:focus {{
    border: 1.5px solid {COLORS['primary']};
}}
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {COLORS['input_border']};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: transparent;
}}
QDateEdit::down-arrow {{
    image: url({_ASSETS}/arrow_down.svg);
    width: 12px;
    height: 8px;
}}
"""

# ---------------------------------------------------------------------------
# TABLEAUX
# ---------------------------------------------------------------------------
TABLE_STYLE = f"""
QTableWidget {{
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border_soft']};
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    font-size: 13px;
    alternate-background-color: {COLORS['table_row_alt']};
    selection-background-color: {COLORS['table_selected']};
    selection-color: {COLORS['text']};
    outline: none;
}}
QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['table_selected']};
    color: {COLORS['text']};
}}
QHeaderView::section {{
    background-color: {COLORS['table_header']};
    padding: 7px 10px;
    font-weight: bold;
    font-size: 13px;
    color: {COLORS['text_soft']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 2px solid {COLORS['border']};
}}
QHeaderView::section:first {{ border-top-left-radius: 6px; }}
QHeaderView::section:last {{ border-top-right-radius: 6px; border-right: none; }}
"""
STYLE_TABLE = TABLE_STYLE

TABLE_STYLE_YELLOW = f"""
QTableWidget {{
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border_soft']};
    background-color: {COLORS['card']};
    color: {COLORS['text']};
    font-size: 13px;
    alternate-background-color: {COLORS['table_alt_yellow']};
    selection-background-color: {COLORS['table_selected']};
    selection-color: {COLORS['text']};
    outline: none;
}}
QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['table_selected']};
    color: {COLORS['text']};
}}
QHeaderView::section {{
    background-color: {COLORS['table_header']};
    padding: 7px 10px;
    font-weight: bold;
    font-size: 13px;
    color: {COLORS['text_soft']};
    border: none;
    border-right: 1px solid {COLORS['border']};
    border-bottom: 2px solid {COLORS['border']};
}}
"""

# ---------------------------------------------------------------------------
# ONGLETS
# ---------------------------------------------------------------------------
TAB_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['card']};
    border-radius: 0 6px 6px 6px;
}}
QTabBar::tab {{
    background-color: {COLORS['surface_soft']};
    color: {COLORS['muted']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 9px 20px;
    font-weight: 500;
    font-size: 14px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}}
QTabBar::tab:hover {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['text']};
}}
QTabBar::tab:selected {{
    background-color: {COLORS['card']};
    color: {COLORS['primary_dark']};
    font-weight: bold;
    border-bottom: 2px solid {COLORS['primary']};
}}
"""

TAB_STYLE_NESTED = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['card']};
}}
QTabBar::tab {{
    background-color: {COLORS['surface_soft']};
    color: #475569;
    border: 1px solid {COLORS['border']};
    padding: 7px 15px;
    font-size: 13px;
    font-weight: 500;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:hover {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['primary_dark']};
}}
QTabBar::tab:selected {{
    background-color: {COLORS['card']};
    color: {COLORS['primary']};
    font-weight: bold;
    border-bottom: 2px solid {COLORS['primary']};
}}
"""

# ---------------------------------------------------------------------------
# BOUTONS
# ---------------------------------------------------------------------------
BUTTON_PRIMARY = f"""
QPushButton {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    padding: 5px 16px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
QPushButton:pressed {{ background-color: #1E3A8A; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""
STYLE_BUTTON_PRIMARY = BUTTON_PRIMARY
BUTTON_STYLE = BUTTON_PRIMARY

BUTTON_SUCCESS = f"""
QPushButton {{
    background-color: {COLORS['success']};
    color: #FFFFFF;
    padding: 5px 16px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{ background-color: #15803D; }}
QPushButton:pressed {{ background-color: #166534; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""
STYLE_BUTTON_SUCCESS = BUTTON_SUCCESS

BUTTON_DANGER = f"""
QPushButton {{
    background-color: {COLORS['danger']};
    color: #FFFFFF;
    padding: 5px 14px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{ background-color: #B91C1C; }}
QPushButton:pressed {{ background-color: #991B1B; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""
STYLE_BUTTON_DANGER = BUTTON_DANGER

BUTTON_SECONDARY = f"""
QPushButton {{
    background-color: {COLORS['surface_soft']};
    color: {COLORS['text_soft']};
    padding: 5px 16px;
    font-weight: 600;
    font-size: 15px;
    border-radius: 7px;
    border: 1px solid {COLORS['border']};
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{
    background-color: {COLORS['border']};
    color: {COLORS['text']};
}}
QPushButton:pressed {{ background-color: #D1D5DB; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; border-color: #E5E7EB; }}
"""
STYLE_BUTTON_SECONDARY = BUTTON_SECONDARY

BUTTON_WARNING = f"""
QPushButton {{
    background-color: {COLORS['warning']};
    color: #FFFFFF;
    padding: 5px 16px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{ background-color: #EA580C; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

BUTTON_PRINT = f"""
QPushButton {{
    background-color: #0F766E;
    color: #FFFFFF;
    padding: 5px 16px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}}
QPushButton:hover {{ background-color: #0D9488; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

BUTTON_TABLE_ACTION = f"""
QPushButton {{
    background-color: {COLORS['border']};
    color: {COLORS['text_soft']};
    padding: 3px 10px;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    border: 1px solid {COLORS['border']};
    min-height: 26px;
    max-height: 30px;
}}
QPushButton:hover {{
    background-color: #CBD5E1;
    color: {COLORS['text']};
}}
"""

BUTTON_TABLE_ACTION_PRIMARY = f"""
QPushButton {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    border: none;
    min-height: 26px;
    max-height: 30px;
}}
QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

BUTTON_TABLE_ACTION_DANGER = f"""
QPushButton {{
    background-color: {COLORS['danger']};
    color: #FFFFFF;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    border: none;
    min-height: 26px;
    max-height: 30px;
}}
QPushButton:hover {{ background-color: #B91C1C; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

BUTTON_TABLE_ACTION_WARNING = f"""
QPushButton {{
    background-color: {COLORS['warning']};
    color: #FFFFFF;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 13px;
    border-radius: 6px;
    border: none;
    min-height: 26px;
    max-height: 30px;
}}
QPushButton:hover {{ background-color: #EA580C; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""

# ---------------------------------------------------------------------------
# MESSAGEBOX / DIALOG — texte foncé sur fond clair, bouton OK lisible
# ---------------------------------------------------------------------------
MESSAGEBOX_STYLE = f"""
QMessageBox {{
    background-color: #FFFFFF;
    color: {COLORS['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 15px;
}}
QMessageBox QLabel {{
    color: {COLORS['text']};
    background-color: transparent;
    font-size: 15px;
    font-weight: normal;
    border: none;
}}
QMessageBox QPushButton {{
    background-color: {COLORS['surface_soft']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['input_border']};
    border-radius: 7px;
    padding: 5px 18px;
    min-width: 80px;
    min-height: 30px;
    max-height: 34px;
    font-size: 15px;
    font-weight: 600;
}}
QMessageBox QPushButton:hover {{
    background-color: {COLORS['border']};
    border-color: {COLORS['muted']};
}}
QMessageBox QPushButton:pressed {{
    background-color: #D1D5DB;
}}
QMessageBox QPushButton:default {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    border-color: {COLORS['primary']};
}}
QMessageBox QPushButton:default:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
QMessageBox QFrame {{
    background-color: transparent;
    border: none;
}}
QDialog {{
    background-color: #FFFFFF;
    color: {COLORS['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 15px;
}}
QDialog QLabel {{
    color: {COLORS['text']};
    background-color: transparent;
    font-size: 14px;
    border: none;
}}
QDialog QPushButton {{
    font-size: 15px;
    font-weight: 600;
    min-height: 30px;
    max-height: 36px;
    padding: 5px 16px;
    border-radius: 7px;
}}
QDialogButtonBox QPushButton {{
    background-color: {COLORS['surface_soft']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['input_border']};
    border-radius: 7px;
    padding: 5px 18px;
    min-width: 80px;
    min-height: 30px;
    max-height: 34px;
    font-size: 15px;
    font-weight: 600;
}}
QDialogButtonBox QPushButton:hover {{
    background-color: {COLORS['border']};
}}
QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="Oui"],
QDialogButtonBox QPushButton[text="Yes"] {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    border-color: {COLORS['primary']};
}}
QDialogButtonBox QPushButton[text="OK"]:hover,
QDialogButtonBox QPushButton[text="Oui"]:hover,
QDialogButtonBox QPushButton[text="Yes"]:hover {{
    background-color: {COLORS['primary_dark']};
}}
"""

# ---------------------------------------------------------------------------
# BADGES
# ---------------------------------------------------------------------------
BADGE_SUCCESS = (
    f"color: {COLORS['success']}; font-weight: bold; font-size: 12px;"
    "background-color: #DCFCE7; border-radius: 10px; padding: 2px 9px;"
)
BADGE_WARNING = (
    f"color: #D97706; font-weight: bold; font-size: 12px;"
    "background-color: #FEF3C7; border-radius: 10px; padding: 2px 9px;"
)
BADGE_DANGER = (
    f"color: {COLORS['danger']}; font-weight: bold; font-size: 12px;"
    "background-color: #FEE2E2; border-radius: 10px; padding: 2px 9px;"
)
BADGE_INFO = (
    f"color: {COLORS['primary']}; font-weight: bold; font-size: 12px;"
    "background-color: #DBEAFE; border-radius: 10px; padding: 2px 9px;"
)

# ---------------------------------------------------------------------------
# GROUPBOX
# ---------------------------------------------------------------------------
GROUPBOX_STYLE = f"""
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
    font-size: 13px;
}}
"""

GROUPBOX_ACCENT_STYLE = f"""
QGroupBox {{
    font-weight: bold;
    font-size: 13px;
    color: {COLORS['primary_dark']};
    border: 1px solid {COLORS['border']};
    border-top: 2px solid {COLORS['primary']};
    border-radius: 6px;
    margin-top: 14px;
    background-color: {COLORS['card']};
    padding-top: 6px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {COLORS['primary_dark']};
    background-color: {COLORS['card']};
    font-size: 13px;
}}
"""

# ---------------------------------------------------------------------------
# MODAL
# ---------------------------------------------------------------------------
MODAL_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg']};
}}
"""

# ---------------------------------------------------------------------------
# PLACEHOLDER / EMPTY STATE
# ---------------------------------------------------------------------------
PLACEHOLDER_STYLE = (
    f"color: {COLORS['muted']}; font-size: 14px; padding: 30px; background-color: transparent;"
)

EMPTY_STATE_STYLE = (
    f"color: {COLORS['muted']}; font-size: 14px; background-color: transparent;"
)

# ---------------------------------------------------------------------------
# BANDEAU (ciblé uniquement via QFrame#bandeau)
# ---------------------------------------------------------------------------
STYLE_BANDEAU = f"""
QFrame#bandeau {{
    background-color: {COLORS['surface_soft']};
    border-bottom: 2px solid {COLORS['primary']};
    border-radius: 8px;
    padding: 10px;
}}
"""

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
    from PySide6.QtWidgets import QAbstractItemView, QHeaderView
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
        }}
        QPushButton:hover {{
            background-color: {COLORS['border']};
            color: {COLORS['text']};
        }}
        QPushButton:pressed {{
            background-color: #D1D5DB;
        }}
        QPushButton:default {{
            background-color: {COLORS['primary']};
            color: #FFFFFF;
            border-color: {COLORS['primary']};
        }}
        QPushButton:default:hover {{
            background-color: {COLORS['primary_dark']};
        }}
    """)


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
    button.setFixedHeight(30)
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
    from PySide6.QtCore import Qt
    container = QWidget()
    container.setStyleSheet("background-color: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(4, 3, 4, 3)
    layout.setSpacing(0)
    layout.addStretch(1)
    layout.addWidget(button)
    layout.addStretch(1)
    return container
