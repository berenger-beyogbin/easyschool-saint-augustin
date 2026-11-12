from ._colors import COLORS

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

BUTTON_PRINT = """
QPushButton {
    background-color: #0F766E;
    color: #FFFFFF;
    padding: 5px 16px;
    font-weight: 700;
    font-size: 15px;
    border-radius: 7px;
    border: none;
    min-height: 32px;
    max-height: 36px;
}
QPushButton:hover { background-color: #0D9488; }
QPushButton:disabled { background-color: #E5E7EB; color: #9CA3AF; }
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
}}
QPushButton:hover {{ background-color: #EA580C; }}
QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
"""
