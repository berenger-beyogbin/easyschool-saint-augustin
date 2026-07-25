# Design system Easy School 2.0 — Amélioration IHM Nette v3
# Toutes les constantes et helpers visuels centralisés ici.

from ._colors import (
    COLORS,
    COLOR_PRIMARY_BLUE, COLOR_LIGHT_BLUE, COLOR_WHITE,
    COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_DANGER,
)
from ._layout import (
    APP_STYLE, SIDEBAR_STYLE, SIDEBAR_MENU_STYLE, TOPBAR_STYLE,
    PAGE_CONTAINER_STYLE, MODULE_HEADER_STYLE, MODAL_STYLE, STYLE_BANDEAU,
)
from ._typography import (
    PAGE_TITLE_STYLE, PAGE_SUBTITLE_STYLE, SECTION_TITLE_STYLE,
    LABEL_STYLE, STYLE_LABEL_TITLE, STYLE_LABEL_SUBTITLE, STYLE_LABEL,
    PANEL_TITLE_STYLE, FIELD_LABEL_STYLE, SECTION_LABEL_STYLE,
    INFO_LABEL_STYLE, MUTED_LABEL_STYLE, VALUE_LABEL_STYLE,
    BADGE_SUCCESS, BADGE_WARNING, BADGE_DANGER, BADGE_INFO,
    PLACEHOLDER_STYLE, EMPTY_STATE_STYLE,
)
from ._cards import (
    CARD_STYLE, SECTION_CARD_STYLE, KPI_CARD_STYLE, SECTION_HEADER_STYLE,
    FINANCIAL_SECTION_STYLE, FORM_SECTION_STYLE, PANEL_CARD_STYLE,
    GROUPBOX_STYLE, GROUPBOX_ACCENT_STYLE,
)
from ._inputs import (
    INPUT_STYLE, STYLE_LINEEDIT, COMBO_STYLE, STYLE_COMBOBOX, DATE_STYLE,
)
from ._tables import (
    TABLE_STYLE, STYLE_TABLE, TABLE_STYLE_YELLOW, TAB_STYLE, TAB_STYLE_NESTED,
)
from ._buttons import (
    BUTTON_PRIMARY, STYLE_BUTTON_PRIMARY, BUTTON_STYLE,
    BUTTON_SUCCESS, STYLE_BUTTON_SUCCESS,
    BUTTON_DANGER, STYLE_BUTTON_DANGER,
    BUTTON_SECONDARY, STYLE_BUTTON_SECONDARY,
    BUTTON_WARNING, BUTTON_PRINT,
    BUTTON_TABLE_ACTION, BUTTON_TABLE_ACTION_PRIMARY,
    BUTTON_TABLE_ACTION_DANGER, BUTTON_TABLE_ACTION_WARNING,
)
from ._dialogs import MESSAGEBOX_STYLE
from ._helpers import (
    apply_table_style, apply_financial_table_style, apply_form_section_style,
    apply_modal_style, install_messagebox_autostyle, apply_card_shadow,
    make_title_label, make_section_label, make_section_title,
    make_placeholder_message, format_fcfa,
    configure_button, configure_table_action_button, make_field_label,
    configure_compact_input, configure_search_input,
    make_stat_card, make_totaux_panel_widget, make_table_action_container,
)

__all__ = [
    "COLORS",
    "COLOR_PRIMARY_BLUE", "COLOR_LIGHT_BLUE", "COLOR_WHITE",
    "COLOR_TEXT_MAIN", "COLOR_TEXT_MUTED", "COLOR_BORDER", "COLOR_DANGER",
    "APP_STYLE", "SIDEBAR_STYLE", "SIDEBAR_MENU_STYLE", "TOPBAR_STYLE",
    "PAGE_CONTAINER_STYLE", "MODULE_HEADER_STYLE", "MODAL_STYLE", "STYLE_BANDEAU",
    "PAGE_TITLE_STYLE", "PAGE_SUBTITLE_STYLE", "SECTION_TITLE_STYLE",
    "LABEL_STYLE", "STYLE_LABEL_TITLE", "STYLE_LABEL_SUBTITLE", "STYLE_LABEL",
    "PANEL_TITLE_STYLE", "FIELD_LABEL_STYLE", "SECTION_LABEL_STYLE",
    "INFO_LABEL_STYLE", "MUTED_LABEL_STYLE", "VALUE_LABEL_STYLE",
    "BADGE_SUCCESS", "BADGE_WARNING", "BADGE_DANGER", "BADGE_INFO",
    "PLACEHOLDER_STYLE", "EMPTY_STATE_STYLE",
    "CARD_STYLE", "SECTION_CARD_STYLE", "KPI_CARD_STYLE", "SECTION_HEADER_STYLE",
    "FINANCIAL_SECTION_STYLE", "FORM_SECTION_STYLE", "PANEL_CARD_STYLE",
    "GROUPBOX_STYLE", "GROUPBOX_ACCENT_STYLE",
    "INPUT_STYLE", "STYLE_LINEEDIT", "COMBO_STYLE", "STYLE_COMBOBOX", "DATE_STYLE",
    "TABLE_STYLE", "STYLE_TABLE", "TABLE_STYLE_YELLOW", "TAB_STYLE", "TAB_STYLE_NESTED",
    "BUTTON_PRIMARY", "STYLE_BUTTON_PRIMARY", "BUTTON_STYLE",
    "BUTTON_SUCCESS", "STYLE_BUTTON_SUCCESS",
    "BUTTON_DANGER", "STYLE_BUTTON_DANGER",
    "BUTTON_SECONDARY", "STYLE_BUTTON_SECONDARY",
    "BUTTON_WARNING", "BUTTON_PRINT",
    "BUTTON_TABLE_ACTION", "BUTTON_TABLE_ACTION_PRIMARY",
    "BUTTON_TABLE_ACTION_DANGER", "BUTTON_TABLE_ACTION_WARNING",
    "MESSAGEBOX_STYLE",
    "apply_table_style", "apply_financial_table_style", "apply_form_section_style",
    "apply_modal_style", "install_messagebox_autostyle", "apply_card_shadow",
    "make_title_label", "make_section_label", "make_section_title",
    "make_placeholder_message", "format_fcfa",
    "configure_button", "configure_table_action_button", "make_field_label",
    "configure_compact_input", "configure_search_input",
    "make_stat_card", "make_totaux_panel_widget", "make_table_action_container",
]
