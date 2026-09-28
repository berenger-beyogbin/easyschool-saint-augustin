from ._colors import COLORS, _ASSETS

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
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['selection']};
    color: {COLORS['text']};
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
