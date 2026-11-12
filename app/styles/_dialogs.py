from ._colors import COLORS

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
    outline: none;
}}
QMessageBox QPushButton:hover {{
    background-color: {COLORS['border']};
    border-color: {COLORS['muted']};
    color: {COLORS['text']};
}}
QMessageBox QPushButton:pressed {{
    background-color: #D1D5DB;
    color: {COLORS['text']};
}}
QMessageBox QPushButton:default {{
    background-color: {COLORS['primary']};
    color: #FFFFFF;
    border-color: {COLORS['primary']};
}}
QMessageBox QPushButton:default:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
    color: #FFFFFF;
}}
QMessageBox QPushButton:default:pressed {{
    background-color: #1E3A8A;
    border-color: #1E3A8A;
    color: #FFFFFF;
}}
QMessageBox QPushButton:focus {{
    color: {COLORS['text']};
}}
QMessageBox QPushButton:default:focus {{
    color: #FFFFFF;
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
