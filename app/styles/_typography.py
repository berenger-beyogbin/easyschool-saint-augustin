from ._colors import COLORS

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
# BADGES
# ---------------------------------------------------------------------------
BADGE_SUCCESS = (
    f"color: {COLORS['success']}; font-weight: bold; font-size: 12px;"
    "background-color: #DCFCE7; border-radius: 10px; padding: 2px 9px;"
)
BADGE_WARNING = (
    "color: #D97706; font-weight: bold; font-size: 12px;"
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
# PLACEHOLDER / EMPTY STATE
# ---------------------------------------------------------------------------
PLACEHOLDER_STYLE = (
    f"color: {COLORS['muted']}; font-size: 14px; padding: 30px; background-color: transparent;"
)

EMPTY_STATE_STYLE = (
    f"color: {COLORS['muted']}; font-size: 14px; background-color: transparent;"
)
