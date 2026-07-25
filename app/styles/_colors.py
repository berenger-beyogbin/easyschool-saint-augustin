import pathlib

_ASSETS = str(pathlib.Path(__file__).parent.parent.parent / "assets").replace("\\", "/")

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
