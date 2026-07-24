from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFrame,
    QDateEdit, QAbstractItemView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from services.versement_service import VersementService
from services.inscription_autres_frais_service import InscriptionAutresFraisService
from app.session import AppSession
from app.config import Config
from utils.receipt_printer import ReceiptPrinter
from app.styles import (
    COLORS, INPUT_STYLE, DATE_STYLE, BUTTON_SECONDARY, TABLE_STYLE, apply_card_shadow, format_fcfa
)
from views.ui_components import FinancialSection, FinancialRow, make_separator


# ─── Valeur UI temporaire du reçu (non persistée en base) ────────────────────
# Le mode de paiement n'est pas encore une colonne de VersementScol : la
# caisse encaissant essentiellement des espèces, la valeur est fixée par
# défaut pour le reçu, le temps d'une phase ulterieure dédiée si besoin.
MODE_PAIEMENT_DEFAUT = "Espèce"


def _compute_motif(m_scol: float, m_trans: float, m_cant: float, m_autres: float = 0) -> str:
    """Déduit un motif de paiement simple à partir des montants versés."""
    parts = []
    if m_scol > 0:
        parts.append("Scolarité")
    if m_trans > 0:
        parts.append("Transport")
    if m_cant > 0:
        parts.append("Cantine")
    if m_autres > 0:
        parts.append("Autres frais")
    return " + ".join(parts) if parts else "Scolarité"


# ─── Helpers montants ────────────────────────────────────────────────────────

def _fmt_input(v) -> str:
    """Formate un montant entier avec séparateur de milliers (espace)."""
    try:
        return f"{int(float(v)):,}".replace(",", " ")
    except Exception:
        return "0"

def _parse_input(text: str) -> float:
    """Parse un montant saisi (supporte les espaces comme séparateurs de milliers)."""
    return float(text.replace(" ", "").replace(",", "").strip() or 0)


# ─── Styles chip ─────────────────────────────────────────────────────────────

_CHIP_MUTED = (
    f"font-size: 11px; font-weight: 600; color: {COLORS['muted']};"
    f"background-color: {COLORS['border_soft']}; border: 1px solid {COLORS['border']};"
    "border-radius: 10px; padding: 3px 10px;"
)
_CHIP_SUCCESS = (
    f"font-size: 11px; font-weight: 600; color: {COLORS['success']};"
    "background-color: #DCFCE7; border: 1px solid #86EFAC;"
    "border-radius: 10px; padding: 3px 10px;"
)

_FRAIS_LIST_STYLE = f"""
QListWidget {{
    background-color: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    outline: none;
    font-size: 12px;
    color: {COLORS['text_soft']};
}}
QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:hover {{
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['input_border']};
    border-radius: 4px;
    background-color: {COLORS['card']};
}}
QListWidget::indicator:unchecked:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_soft']};
}}
QListWidget::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QListWidget::indicator:checked:hover {{
    background-color: {COLORS['primary_dark']};
    border-color: {COLORS['primary_dark']};
}}
"""


# ─── Widget toggle ON/OFF ────────────────────────────────────────────────────

class ToggleSwitch(QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(64, 30)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
        self.toggled.connect(lambda _: self._apply_style())

    def _apply_style(self):
        if self.isChecked():
            self.setText("ON")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #16A34A;
                    color: #FFFFFF;
                    border-radius: 15px;
                    font-size: 10px;
                    font-weight: 800;
                    border: none;
                    letter-spacing: 1px;
                }
                QPushButton:hover { background-color: #15803D; }
            """)
        else:
            self.setText("OFF")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #CBD5E1;
                    color: #64748B;
                    border-radius: 15px;
                    font-size: 10px;
                    font-weight: 800;
                    border: none;
                    letter-spacing: 1px;
                }
                QPushButton:hover { background-color: #94A3B8; }
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._apply_style()


# ─── Helpers UI ──────────────────────────────────────────────────────────────

def _make_field_group(label_text: str, widget) -> QVBoxLayout:
    """Label uppercase + champ de saisie."""
    vbox = QVBoxLayout()
    vbox.setContentsMargins(0, 0, 0, 0)
    vbox.setSpacing(2)
    lbl = QLabel(label_text.upper())
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 700; color: #94A3B8;"
        "background-color: transparent; border: none; letter-spacing: 0.8px;"
    )
    # Le libellé ne doit jamais forcer le groupe à dépasser la largeur du champ
    # (ex. « AUTRES FRAIS » plus long que le QLineEdit de 130px) :
    # il se limite à cette largeur et passe à la ligne au besoin.
    field_width = widget.maximumWidth()
    if 0 < field_width < 16777215:
        lbl.setFixedWidth(field_width)
        lbl.setWordWrap(True)
    vbox.addWidget(lbl)
    vbox.addWidget(widget)
    return vbox


def _make_panel(accent_color: str) -> tuple:
    """Retourne (QFrame card, QVBoxLayout content) avec top-accent + ombre."""
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-top: 3px solid {accent_color};
            border-radius: 10px;
        }}
    """)
    apply_card_shadow(card)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)
    return card, layout


# ─── Vue principale ──────────────────────────────────────────────────────────

class CaisseView(QWidget):

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_eleve_id = None
        self.selected_famille_id = None
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.setSpacing(16)

        # ─── COLONNE GAUCHE (~72%) ───────────────────────────────────────────
        col_gauche = QWidget()
        col_gauche.setStyleSheet("background-color: transparent;")
        layout_gauche = QVBoxLayout(col_gauche)
        layout_gauche.setContentsMargins(0, 0, 0, 0)
        layout_gauche.setSpacing(14)

        self._build_search_panel(layout_gauche)
        self._build_versement_panel(layout_gauche)
        self._build_history_panel(layout_gauche)

        layout_principal.addWidget(col_gauche, 18)

        # ─── COLONNE DROITE (~28%) ───────────────────────────────────────────
        col_droite = QWidget()
        col_droite.setStyleSheet("background-color: transparent;")
        layout_droite = QVBoxLayout(col_droite)
        layout_droite.setContentsMargins(0, 0, 0, 0)
        layout_droite.setSpacing(0)

        self._build_financial_panel(layout_droite)

        layout_principal.addWidget(col_droite, 7)

        self.load_eleves()

    # -------------------------------------------------------------------------
    # PANNEAU RECHERCHE
    # -------------------------------------------------------------------------

    def _build_search_panel(self, parent_layout):
        panel, layout = _make_panel(COLORS['primary'])

        # Barre de recherche
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.txt_recherche = QLineEdit()
        self.txt_recherche.setPlaceholderText("Nom, prénom ou matricule…")
        self.txt_recherche.setStyleSheet(INPUT_STYLE)
        self.txt_recherche.setFixedHeight(36)
        self.txt_recherche.textChanged.connect(self.on_search_changed)
        search_row.addWidget(self.txt_recherche, 1, Qt.AlignVCenter)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setStyleSheet(BUTTON_SECONDARY)
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.setFixedWidth(110)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_eleves)
        search_row.addWidget(self.btn_refresh, 0, Qt.AlignVCenter)

        layout.addLayout(search_row)

        # Tableau élèves
        self.table_eleves = QTableWidget()
        self.table_eleves.setColumnCount(6)
        self.table_eleves.setHorizontalHeaderLabels([
            "Matricule", "Nom & Prénoms", "Classe", "Cantine", "Transport", "Nouveau"
        ])
        if not Config.ENABLE_CANTINE:
            self.table_eleves.setColumnHidden(3, True)
        if not Config.ENABLE_TRANSPORT:
            self.table_eleves.setColumnHidden(4, True)
        self.table_eleves.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_eleves.setSelectionMode(QTableWidget.SingleSelection)
        self.table_eleves.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_eleves.setAlternatingRowColors(True)
        self.table_eleves.setStyleSheet(TABLE_STYLE)
        self.table_eleves.verticalHeader().setVisible(False)
        self.table_eleves.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_eleves.horizontalHeader().setHighlightSections(False)
        self.table_eleves.setFixedHeight(155)
        self.table_eleves.setFrameShape(QFrame.NoFrame)
        self.table_eleves.setShowGrid(False)
        self.table_eleves.itemSelectionChanged.connect(self.on_eleve_selected)
        layout.addWidget(self.table_eleves)

        parent_layout.addWidget(panel)

    # -------------------------------------------------------------------------
    # PANNEAU VERSEMENT
    # -------------------------------------------------------------------------

    def _build_versement_panel(self, parent_layout):
        self.panel_versement, layout = _make_panel(COLORS['success'])
        self.panel_versement.setEnabled(False)

        # Titre + chip élève sélectionné
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(12)

        lbl_t = QLabel("Enregistrer un versement")
        lbl_t.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        header_row.addWidget(lbl_t, 1)

        self.lbl_target_student = QLabel("Aucun élève sélectionné")
        self.lbl_target_student.setStyleSheet(_CHIP_MUTED)
        self.lbl_target_student.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(self.lbl_target_student)
        layout.addLayout(header_row)

        layout.addWidget(make_separator())

        # Corps du formulaire : un unique bandeau horizontal regroupant tous
        # les champs (montants + paiement), pour limiter la hauteur de cette
        # carte et laisser un maximum de place au tableau d'historique en
        # dessous. Champs volontairement compacts (FIELD_H/AMOUNT_W réduits).
        FIELD_H = 32
        AMOUNT_W = 130

        form_row = QHBoxLayout()
        form_row.setSpacing(12)

        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDisplayFormat("dd/MM/yyyy")
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setStyleSheet(DATE_STYLE)
        self.txt_date.setFixedWidth(AMOUNT_W + 30)
        self.txt_date.setFixedHeight(FIELD_H)
        grp_date = _make_field_group("Date", self.txt_date)
        form_row.addLayout(grp_date)
        form_row.setAlignment(grp_date, Qt.AlignTop)

        self.txt_vers_scol = QLineEdit("0")
        self.txt_vers_scol.setStyleSheet(INPUT_STYLE)
        self.txt_vers_scol.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_vers_scol.setFixedWidth(AMOUNT_W)
        self.txt_vers_scol.setFixedHeight(FIELD_H)
        self.txt_vers_scol.textChanged.connect(lambda: self._format_amount_field(self.txt_vers_scol))
        grp_scol = _make_field_group("Scolarité", self.txt_vers_scol)
        form_row.addLayout(grp_scol)
        form_row.setAlignment(grp_scol, Qt.AlignTop)

        self.txt_vers_trans = QLineEdit("0")
        self.txt_vers_trans.setStyleSheet(INPUT_STYLE)
        self.txt_vers_trans.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_vers_trans.setFixedWidth(AMOUNT_W)
        self.txt_vers_trans.setFixedHeight(FIELD_H)
        self.txt_vers_trans.textChanged.connect(lambda: self._format_amount_field(self.txt_vers_trans))
        # Transport désactivé pour la version collège CJGA — champ masqué,
        # la valeur interne reste "0" (aucune saisie possible).
        self.grp_vers_trans = QWidget()
        self.grp_vers_trans.setStyleSheet("background-color: transparent; border: none;")
        self.grp_vers_trans.setLayout(_make_field_group("Transport", self.txt_vers_trans))
        self.grp_vers_trans.setVisible(Config.ENABLE_TRANSPORT)
        form_row.addWidget(self.grp_vers_trans)
        form_row.setAlignment(self.grp_vers_trans, Qt.AlignTop)

        self.txt_vers_cant = QLineEdit("0")
        self.txt_vers_cant.setStyleSheet(INPUT_STYLE)
        self.txt_vers_cant.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.txt_vers_cant.setFixedWidth(AMOUNT_W)
        self.txt_vers_cant.setFixedHeight(FIELD_H)
        self.txt_vers_cant.textChanged.connect(lambda: self._format_amount_field(self.txt_vers_cant))
        # Cantine désactivée pour la version collège CJGA — champ masqué,
        # la valeur interne reste "0" (aucune saisie possible).
        self.grp_vers_cant = QWidget()
        self.grp_vers_cant.setStyleSheet("background-color: transparent; border: none;")
        self.grp_vers_cant.setLayout(_make_field_group("Cantine", self.txt_vers_cant))
        self.grp_vers_cant.setVisible(Config.ENABLE_CANTINE)
        form_row.addWidget(self.grp_vers_cant)
        form_row.setAlignment(self.grp_vers_cant, Qt.AlignTop)

        form_row.addStretch(1)

        # Bloc "Autres frais" : liste cochable des frais annexes retenus à
        # l'inscription de l'élève, pour que la caissière sélectionne ceux
        # que ce versement couvre. Masqué si l'élève n'a aucun frais annexe.
        self.grp_autres_frais = QWidget()
        self.grp_autres_frais.setStyleSheet("background-color: transparent; border: none;")
        autres_layout = QVBoxLayout(self.grp_autres_frais)
        autres_layout.setContentsMargins(0, 0, 0, 0)
        autres_layout.setSpacing(2)

        lbl_autres = QLabel("AUTRES FRAIS À VERSER")
        lbl_autres.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #94A3B8;"
            "background-color: transparent; border: none; letter-spacing: 0.8px;"
        )
        autres_layout.addWidget(lbl_autres)

        self.list_autres_frais = QListWidget()
        self.list_autres_frais.setStyleSheet(_FRAIS_LIST_STYLE)
        self.list_autres_frais.setFrameShape(QFrame.NoFrame)
        self.list_autres_frais.setFixedWidth(280)
        self.list_autres_frais.setFixedHeight(2 * FIELD_H + 22)
        self.list_autres_frais.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_autres_frais.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_autres_frais.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_autres_frais.setFocusPolicy(Qt.NoFocus)
        self.list_autres_frais.itemChanged.connect(self._update_autres_frais_total)
        autres_layout.addWidget(self.list_autres_frais)

        self.lbl_total_autres_frais = QLabel("Total sélectionné : 0 FCFA")
        self.lbl_total_autres_frais.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {COLORS['purple']};"
            "background-color: transparent; border: none;"
        )
        autres_layout.addWidget(self.lbl_total_autres_frais)

        self._autres_frais_items = []
        self.grp_autres_frais.setVisible(False)
        form_row.addWidget(self.grp_autres_frais)
        form_row.setAlignment(self.grp_autres_frais, Qt.AlignTop)

        form_row.addStretch(1)

        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(4)
        btn_vbox.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        lbl_reduc = QLabel("RÉDUCTION")
        lbl_reduc.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #94A3B8;"
            "background-color: transparent; border: none; letter-spacing: 0.8px;"
        )
        lbl_reduc.setAlignment(Qt.AlignHCenter)
        self.toggle_reduction = ToggleSwitch()
        btn_vbox.addWidget(lbl_reduc, 0, Qt.AlignHCenter)
        btn_vbox.addWidget(self.toggle_reduction, 0, Qt.AlignHCenter)
        btn_vbox.addSpacing(10)

        self.btn_valider_versement = QPushButton("✓  Valider")
        self.btn_valider_versement.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: #FFFFFF;
                padding: 0 20px;
                font-weight: 700;
                font-size: 13px;
                border-radius: 8px;
                border: none;
                min-height: 32px;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{ background-color: #15803D; }}
            QPushButton:pressed {{ background-color: #166534; }}
            QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
        """)
        self.btn_valider_versement.setMinimumWidth(130)
        self.btn_valider_versement.setCursor(Qt.PointingHandCursor)
        self.btn_valider_versement.setEnabled(False)
        self.btn_valider_versement.clicked.connect(self.on_validate_and_save)
        btn_vbox.addWidget(self.btn_valider_versement)
        form_row.addLayout(btn_vbox)

        layout.addLayout(form_row)
        parent_layout.addWidget(self.panel_versement)

    # -------------------------------------------------------------------------
    # PANNEAU HISTORIQUE
    # -------------------------------------------------------------------------

    def _build_history_panel(self, parent_layout):
        panel, layout = _make_panel("#475569")
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(7)
        self.table_history.setHorizontalHeaderLabels([
            "Date", "Scolarité", "Autres frais", "Transport", "Cantine", "Réduc.", "ID"
        ])
        if not Config.ENABLE_TRANSPORT:
            self.table_history.setColumnHidden(3, True)
        if not Config.ENABLE_CANTINE:
            self.table_history.setColumnHidden(4, True)
        self.table_history.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_history.setSelectionMode(QTableWidget.SingleSelection)
        self.table_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setStyleSheet(TABLE_STYLE + "QTableWidget { border: none; }")
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.horizontalHeader().setHighlightSections(False)
        self.table_history.setColumnHidden(6, True)
        self.table_history.setFrameShape(QFrame.NoFrame)
        self.table_history.setShowGrid(False)
        layout.addWidget(self.table_history)

        parent_layout.addWidget(panel, 1)

    # -------------------------------------------------------------------------
    # PANNEAU FINANCIER (colonne droite)
    # -------------------------------------------------------------------------

    def _build_financial_panel(self, parent_layout):
        outer = QFrame()
        outer.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        apply_card_shadow(outer)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # En-tête gradient
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary_dark']}, stop:1 #1E40AF);
                border-radius: 12px 12px 0 0;
                border: none;
            }}
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(18, 14, 18, 14)
        h_layout.setSpacing(3)

        lbl_h = QLabel("Situation financière")
        lbl_h.setStyleSheet(
            "font-size: 13px; font-weight: 800; color: #FFFFFF;"
            "background-color: transparent; border: none;"
        )
        h_layout.addWidget(lbl_h)

        self.lbl_fin_eleve = QLabel("—")
        self.lbl_fin_eleve.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.80);"
            "background-color: transparent; border: none;"
        )
        h_layout.addWidget(self.lbl_fin_eleve)
        outer_layout.addWidget(header)

        # Corps
        body = QWidget()
        body.setStyleSheet(f"background-color: {COLORS['card']};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(10)

        # Bilan global (fond bleu clair)
        total_frame = QFrame()
        total_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary_soft']};
                border: 1px solid #BFDBFE;
                border-radius: 8px;
            }}
        """)
        total_layout = QVBoxLayout(total_frame)
        total_layout.setContentsMargins(14, 12, 14, 12)
        total_layout.setSpacing(5)

        lbl_total_title = QLabel("BILAN GLOBAL")
        lbl_total_title.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {COLORS['primary']};"
            "background-color: transparent; border: none; letter-spacing: 0.8px;"
        )
        total_layout.addWidget(lbl_total_title)
        total_layout.addWidget(make_separator("#BFDBFE"))

        self.row_tot_due   = FinancialRow("Total dû",    "0 F", bold=True)
        self.row_tot_paid  = FinancialRow("Total versé", "0 F", COLORS["success"], bold=True)
        self.row_tot_reduc = FinancialRow("Réduction",   "0 F", COLORS["purple"])
        self.row_tot_reduc.setVisible(False)
        self.row_tot_rem   = FinancialRow("Reste",       "0 F", COLORS["danger"],  bold=True)

        total_layout.addWidget(self.row_tot_due)
        total_layout.addWidget(self.row_tot_paid)
        total_layout.addWidget(self.row_tot_reduc)
        total_layout.addWidget(self.row_tot_rem)
        body_layout.addWidget(total_frame)

        # Sections par rubrique
        self.fs_scol   = FinancialSection("Scolarité",    COLORS["primary"])
        self.fs_trans  = FinancialSection("Transport",     "#0369A1")
        self.fs_cant   = FinancialSection("Cantine",       COLORS["warning"])
        self.fs_autres = FinancialSection("Autres frais",  COLORS["purple"])

        self.row_sc_due   = self.fs_scol.add_row("Dû",        "0 F")
        self.row_sc_paid  = self.fs_scol.add_row("Versé",     "0 F", COLORS["success"])
        self.row_sc_reduc = self.fs_scol.add_row("Réduction", "0 F", COLORS["purple"])
        self.row_sc_reduc.setVisible(False)
        self.row_sc_rem   = self.fs_scol.add_row("Reste",     "0 F", COLORS["danger"], bold=True)

        self.row_tr_due  = self.fs_trans.add_row("Dû",    "0 F")
        self.row_tr_paid = self.fs_trans.add_row("Versé", "0 F", COLORS["success"])
        self.row_tr_rem  = self.fs_trans.add_row("Reste", "0 F", COLORS["danger"], bold=True)

        self.row_ca_due  = self.fs_cant.add_row("Dû",    "0 F")
        self.row_ca_paid = self.fs_cant.add_row("Versé", "0 F", COLORS["success"])
        self.row_ca_rem  = self.fs_cant.add_row("Reste", "0 F", COLORS["danger"], bold=True)

        self.row_au_due  = self.fs_autres.add_row("Dû",    "0 F")
        self.row_au_paid = self.fs_autres.add_row("Versé", "0 F", COLORS["success"])
        self.row_au_rem  = self.fs_autres.add_row("Reste", "0 F", COLORS["danger"], bold=True)

        self.fs_trans.setVisible(False)
        self.fs_cant.setVisible(False)
        self.fs_autres.setVisible(False)

        body_layout.addWidget(self.fs_scol)
        body_layout.addWidget(self.fs_trans)
        body_layout.addWidget(self.fs_cant)
        body_layout.addWidget(self.fs_autres)

        body_layout.addStretch()

        outer_layout.addWidget(body, 1)
        parent_layout.addWidget(outer, 1)

    # =========================================================================
    # LOGIQUE MÉTIER
    # =========================================================================

    def load_eleves(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return
        inscrits = VersementService.get_eleves_inscrits(active_annee_id)
        self.display_eleves(inscrits)

    def on_search_changed(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return
        query = self.txt_recherche.text().strip()
        if not query:
            self.load_eleves()
            return
        results = VersementService.search_eleves_inscrits(active_annee_id, query)
        self.display_eleves(results)

    def display_eleves(self, items):
        self.table_eleves.setRowCount(len(items))

        for i, qi in enumerate(items):
            m_mat    = qi.eleve.Matricule if qi.eleve else "—"
            m_nom    = f"{qi.eleve.Nom if qi.eleve else ''} {qi.eleve.Prenoms if qi.eleve else ''}".strip()
            m_classe = qi.classe.LibClasse if qi.classe else "Non défini"
            m_cant   = "Oui" if qi.Cantine else "Non"
            m_trans  = "Oui" if qi.Transport else "Non"
            m_nouv   = "Oui" if qi.Nouveau else "Non"

            for col, val in enumerate([m_mat, m_nom, m_classe, m_cant, m_trans, m_nouv]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.UserRole, (qi.IDEleve, qi.IDFamille))
                self.table_eleves.setItem(i, col, item)
                self.table_eleves.setRowHeight(i, 34)

        self.selected_eleve_id = None
        self.selected_famille_id = None
        self.panel_versement.setEnabled(False)
        self.lbl_target_student.setText("Aucun élève sélectionné")
        self.lbl_target_student.setStyleSheet(_CHIP_MUTED)
        self.clear_fields()
        self.clear_financial_panel()

    def on_eleve_selected(self):
        selected_ranges = self.table_eleves.selectedRanges()
        if not selected_ranges:
            return
        row = selected_ranges[0].topRow()
        item_mat = self.table_eleves.item(row, 0)
        item_nom = self.table_eleves.item(row, 1)
        if not item_mat or not item_nom:
            return
        self.selected_eleve_id, self.selected_famille_id = item_mat.data(Qt.UserRole)
        self.lbl_target_student.setText(f"{item_nom.text()}  ·  {item_mat.text()}")
        self.lbl_target_student.setStyleSheet(_CHIP_SUCCESS)
        self.lbl_fin_eleve.setText(f"{item_nom.text()} ({item_mat.text()})")
        self.panel_versement.setEnabled(True)
        self.refresh_eleve_profile()

    def refresh_eleve_profile(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_eleve_id:
            return
        fin = VersementService.get_infos_financieres_eleve(active_annee_id, self.selected_eleve_id)
        self._update_financial_panel(fin)
        opts = fin["options"]

        self.txt_vers_scol.setEnabled(opts["scolarite"]  and fin["scol_reste"]  > 0)
        self.txt_vers_trans.setEnabled(opts["transport"] and fin["trans_reste"] > 0)
        self.txt_vers_cant.setEnabled(opts["cantine"]   and fin["cant_reste"]  > 0)

        self.txt_vers_scol.setText("0" if self.txt_vers_scol.isEnabled() else "")
        self.txt_vers_trans.setText("0" if self.txt_vers_trans.isEnabled() else "")
        self.txt_vers_cant.setText("0" if self.txt_vers_cant.isEnabled() else "")

        self._load_autres_frais_versement(fin.get("id_inscription"))
        self.load_history()

    def _load_autres_frais_versement(self, id_inscription):
        """Recharge la liste cochable des autres frais retenus pour l'inscription de l'élève."""
        self.list_autres_frais.blockSignals(True)
        self.list_autres_frais.clear()
        self._autres_frais_items = []
        self.list_autres_frais.blockSignals(False)

        if not id_inscription:
            self.grp_autres_frais.setVisible(False)
            self._update_autres_frais_total()
            return

        frais_coches = InscriptionAutresFraisService.get_frais_impayes(id_inscription)
        self.grp_autres_frais.setVisible(bool(frais_coches))
        if not frais_coches:
            self._update_autres_frais_total()
            return

        self.list_autres_frais.blockSignals(True)
        for frais in frais_coches:
            libelle = frais.get("LibelleSnapshot") or frais.get("CodeFraisSnapshot") or "Frais"
            montant = frais.get("MontantApplique") or 0
            item = QListWidgetItem(f"{libelle} — {format_fcfa(montant)}")
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_autres_frais.addItem(item)
            self._autres_frais_items.append((item, frais))
        self.list_autres_frais.blockSignals(False)

        # Hauteur ajustée au nombre réel de lignes visibles (2 max, le reste
        # défile) : évite qu'une ligne partiellement affichée ne ressemble à
        # une ligne vide en bas de la liste.
        row_h = self.list_autres_frais.sizeHintForRow(0)
        visible_rows = min(len(frais_coches), 2)
        self.list_autres_frais.setFixedHeight(visible_rows * row_h + 2)

        self._update_autres_frais_total()

    def _update_autres_frais_total(self):
        """Recalcule le total des autres frais coches et rafraîchit l'état du bouton Valider."""
        total = sum(
            float(frais.get("MontantApplique") or 0)
            for item, frais in self._autres_frais_items
            if item.checkState() == Qt.Checked
        )
        self.lbl_total_autres_frais.setText(f"Total sélectionné : {format_fcfa(total)}")
        self._update_valider_button()

    def _get_montant_autres_frais_coches(self) -> float:
        """Somme des montants des autres frais actuellement coches dans la liste de versement."""
        return sum(
            float(frais.get("MontantApplique") or 0)
            for item, frais in self._autres_frais_items
            if item.checkState() == Qt.Checked
        )

    def _update_financial_panel(self, fin):
        def fmt(v):
            try:
                return f"{int(float(v)):,} F".replace(",", " ")
            except Exception:
                return "0 F"

        self.row_sc_due.set_value(fmt(fin["scol_due"]))
        self.row_sc_paid.set_value(fmt(fin["scol_paye"]))
        self.row_sc_reduc.setVisible(fin["scol_reduc"] > 0)
        self.row_sc_reduc.set_value(fmt(fin["scol_reduc"]))
        self.row_sc_rem.set_value(fmt(fin["scol_reste"]))

        self.fs_trans.setVisible(Config.ENABLE_TRANSPORT and fin["trans_due"] > 0)
        self.row_tr_due.set_value(fmt(fin["trans_due"]))
        self.row_tr_paid.set_value(fmt(fin["trans_paye"]))
        self.row_tr_rem.set_value(fmt(fin["trans_reste"]))

        self.fs_cant.setVisible(Config.ENABLE_CANTINE and fin["cant_due"] > 0)
        self.row_ca_due.set_value(fmt(fin["cant_due"]))
        self.row_ca_paid.set_value(fmt(fin["cant_paye"]))
        self.row_ca_rem.set_value(fmt(fin["cant_reste"]))

        self.fs_autres.setVisible(fin["autres_due"] > 0)
        self.row_au_due.set_value(fmt(fin["autres_due"]))
        self.row_au_paid.set_value(fmt(fin["autres_paye"]))
        self.row_au_rem.set_value(fmt(fin["autres_reste"]))

        self.row_tot_due.set_value(fmt(fin["total_due"]))
        self.row_tot_paid.set_value(fmt(fin["total_paye"]))
        self.row_tot_reduc.setVisible(fin["total_reduc"] > 0)
        self.row_tot_reduc.set_value(fmt(fin["total_reduc"]))
        self.row_tot_rem.set_value(fmt(fin["total_reste"]))

        try:
            color = COLORS["danger"] if fin["total_reste"] > 0 else COLORS["success"]
            self.row_tot_rem.set_color(color)
        except Exception:
            pass

    def load_history(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_eleve_id:
            return
        vlist = VersementService.get_versements_eleve(active_annee_id, self.selected_eleve_id)
        self.table_history.setRowCount(len(vlist))

        for i, v in enumerate(vlist):
            dt_str = v.DateVers.strftime("%d/%m/%Y") if v.DateVers else "N/A"
            scol   = int(v.MontantVersSco)
            autres = int(v.MontantVersAutres)
            trans  = int(v.MontantVersTrans)
            cant   = int(v.MontantCantine)
            vals = [
                dt_str,
                f"{scol:,} F".replace(",", " "),
                f"{autres:,} F".replace(",", " "),
                f"{trans:,} F".replace(",", " "),
                f"{cant:,} F".replace(",", " "),
                "Oui" if v.Reduction else "Non",
                str(v.IDVersementScol),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 1:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if scol > 0:
                        item.setForeground(QColor(COLORS['primary']))
                elif col == 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if autres > 0:
                        item.setForeground(QColor(COLORS['purple']))
                elif col == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if trans > 0:
                        item.setForeground(QColor("#0369A1"))
                elif col == 4:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if cant > 0:
                        item.setForeground(QColor(COLORS['warning']))
                self.table_history.setItem(i, col, item)
            self.table_history.setRowHeight(i, 34)

    def on_validate_and_save(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_eleve_id or not self.selected_famille_id:
            QMessageBox.warning(self, "Erreur", "Sélecteur d'élève manquant.")
            return
        q_date = self.txt_date.date().toPython()
        try:
            m_scol   = _parse_input(self.txt_vers_scol.text())
            m_trans  = _parse_input(self.txt_vers_trans.text())
            m_cant   = _parse_input(self.txt_vers_cant.text())
            m_autres = self._get_montant_autres_frais_coches()
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Un des montants saisis est incorrect.")
            return

        ids_autres_frais = [
            frais["IDInscriptionAutresFrais"]
            for item, frais in self._autres_frais_items
            if item.checkState() == Qt.Checked
        ]

        reduction_active = self.toggle_reduction.isChecked()

        # Montants dus AVANT le paiement (pour « Montant dû » sur le reçu)
        fin_before = VersementService.get_infos_financieres_eleve(active_annee_id, self.selected_eleve_id)

        success, msg, new_id = VersementService.create_versement(
            id_annee=active_annee_id,
            id_eleve=self.selected_eleve_id,
            id_famille=self.selected_famille_id,
            date_v=q_date,
            m_scol=m_scol,
            m_trans=m_trans,
            m_cant=m_cant,
            m_autres=m_autres,
            reduction=reduction_active,
            impaye=False,
            restitution=False,
            login=AppSession.get_logged_in_username(),
            ids_autres_frais=ids_autres_frais,
        )
        if success:
            self.toggle_reduction.setChecked(False)
            self.txt_date.setDate(QDate.currentDate())
            self.refresh_eleve_profile()

            if reduction_active:
                # Une réduction n'est jamais un paiement réel : aucun reçu.
                QMessageBox.information(
                    self, "Réduction enregistrée",
                    "Réduction enregistrée avec succès. Aucun reçu n'a été généré."
                )
                return

            # Situation financière APRÈS le paiement (pour « Reste à verser »)
            fin_after = VersementService.get_infos_financieres_eleve(active_annee_id, self.selected_eleve_id)

            # Récupération des infos élève depuis la ligne sélectionnée
            sel_row   = self.table_eleves.selectedRanges()[0].topRow()
            nom_eleve = self.table_eleves.item(sel_row, 1).text()
            mat_eleve = self.table_eleves.item(sel_row, 0).text()
            cls_eleve = self.table_eleves.item(sel_row, 2).text()

            receipt_data = {
                "date": self.txt_date.date().toString("dd/MM/yyyy"),
                "matricule":     mat_eleve,
                "nom":           nom_eleve,
                "classe":        cls_eleve,
                "numero":        str(new_id) if new_id else "—",
                # Enrichissement CJGA — valeurs UI temporaires (non persistées en base)
                "motif":         _compute_motif(m_scol, m_trans, m_cant, m_autres),
                "mode_paiement": MODE_PAIEMENT_DEFAUT,
                "total_recu":    m_scol + m_trans + m_cant + m_autres,
                # SCOLARITE
                "scol_active": fin_before["options"]["scolarite"],
                "scol_due":    fin_before["scol_reste"],   # solde dû AVANT ce paiement
                "scol_recu":   m_scol,
                "scol_reste":  fin_after["scol_reste"],
                # AUTRES FRAIS
                "autres_active": fin_before["autres_due"] > 0 or m_autres > 0,
                "autres_due":    fin_before["autres_reste"],  # solde dû AVANT ce paiement
                "autres_recu":   m_autres,
                "autres_reste":  fin_after["autres_reste"],
                # TRANSPORT
                "trans_active": Config.ENABLE_TRANSPORT and fin_before["options"]["transport"],
                "trans_due":    fin_before["trans_reste"],  # solde dû AVANT ce paiement
                "trans_recu":   m_trans,
                "trans_reste":  fin_after["trans_reste"],
                # CANTINE
                "cant_active": Config.ENABLE_CANTINE and fin_before["options"]["cantine"],
                "cant_due":    fin_before["cant_reste"],    # solde dû AVANT ce paiement
                "cant_recu":   m_cant,
                "cant_reste":  fin_after["cant_reste"],
            }

            # Ouverture de l'aperçu du reçu
            ReceiptPrinter.print_receipt(self, receipt_data)
        else:
            QMessageBox.critical(self, "Erreur de versement", msg)

    def _format_amount_field(self, line_edit: QLineEdit):
        """Reformate en direct un champ montant : chiffres uniquement, séparateur de milliers, curseur en fin."""
        line_edit.blockSignals(True)
        raw = "".join(ch for ch in line_edit.text() if ch.isdigit())
        line_edit.setText(_fmt_input(raw) if raw else "")
        line_edit.setCursorPosition(len(line_edit.text()))
        line_edit.blockSignals(False)
        self._update_valider_button()

    def _update_valider_button(self):
        try:
            total = 0
            if self.txt_vers_scol.isEnabled():
                total += _parse_input(self.txt_vers_scol.text())
            if self.txt_vers_trans.isEnabled():
                total += _parse_input(self.txt_vers_trans.text())
            if self.txt_vers_cant.isEnabled():
                total += _parse_input(self.txt_vers_cant.text())
            total += self._get_montant_autres_frais_coches()
        except Exception:
            total = 0
        self.btn_valider_versement.setEnabled(total > 0)

    def clear_fields(self):
        self.txt_vers_scol.setText("")
        self.txt_vers_trans.setText("")
        self.txt_vers_cant.setText("")
        self._load_autres_frais_versement(None)
        self.table_history.setRowCount(0)

    def clear_financial_panel(self):
        self.lbl_fin_eleve.setText("—")
        for row in [
            self.row_sc_due,  self.row_sc_paid,  self.row_sc_rem,
            self.row_tr_due,  self.row_tr_paid,  self.row_tr_rem,
            self.row_ca_due,  self.row_ca_paid,  self.row_ca_rem,
            self.row_au_due,  self.row_au_paid,  self.row_au_rem,
            self.row_tot_due, self.row_tot_paid, self.row_tot_rem,
        ]:
            row.set_value("0 F")
        self.row_sc_reduc.setVisible(False)
        self.row_tot_reduc.setVisible(False)
        self.fs_trans.setVisible(False)
        self.fs_cant.setVisible(False)
        self.fs_autres.setVisible(False)
        self.grp_autres_frais.setVisible(False)
        self.lbl_total_autres_frais.setText("Total sélectionné : 0 F")
