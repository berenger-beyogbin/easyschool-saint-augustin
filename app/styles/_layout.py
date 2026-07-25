from ._colors import COLORS

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
# MODULE HEADER
# ---------------------------------------------------------------------------
MODULE_HEADER_STYLE = f"""
QFrame#module_header {{
    background-color: {COLORS['card']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 0;
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
