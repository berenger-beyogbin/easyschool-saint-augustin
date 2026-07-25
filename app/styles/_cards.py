from ._colors import COLORS

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
