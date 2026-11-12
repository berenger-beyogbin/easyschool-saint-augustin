from ._colors import COLORS

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
