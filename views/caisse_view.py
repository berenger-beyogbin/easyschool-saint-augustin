from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QFrame,
    QDateEdit, QAbstractItemView, QComboBox
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from services.versement_service import VersementService
from app.session import AppSession
from app.config import Config
from utils.receipt_printer import ReceiptPrinter
from app.styles import (
    COLORS, INPUT_STYLE, DATE_STYLE, BUTTON_SUCCESS,
    BUTTON_SECONDARY, TABLE_STYLE, COMBO_STYLE, apply_card_shadow
)
from views.ui_components import FinancialSection, FinancialRow, make_separator


# ─── Valeurs UI temporaires du reçu (non persistées en base) ─────────────────
# Ces informations ne sont pas encore des colonnes de VersementScol : elles ne
# sont transmises qu'au reçu imprimé, le temps d'une phase ulterieure dédiée.
MODES_PAIEMENT = ["Espèce", "Mobile Money", "Chèque", "Virement"]
TITULAIRES_PAIEMENT = ["Non précisé", "Père", "Mère", "Tuteur", "Autre"]


def _compute_motif(m_scol: float, m_trans: float, m_cant: float) -> str:
    """Déduit un motif de paiement simple à partir des montants versés."""
    parts = []
    if m_scol > 0:
        parts.append("Scolarité")
    if m_trans > 0:
        parts.append("Transport")
    if m_cant > 0:
        parts.append("Cantine")
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
    vbox.setSpacing(4)
    lbl = QLabel(label_text.upper())
    lbl.setStyleSheet(
        "font-size: 10px; font-weight: 700; color: #94A3B8;"
        "background-color: transparent; border: none; letter-spacing: 0.8px;"
    )
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

        # Titre + badge compteur
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)
        lbl_title = QLabel("Rechercher un élève inscrit")
        lbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        lbl_sub = QLabel("Cliquez sur une ligne pour accéder aux informations financières")
        lbl_sub.setStyleSheet(
            f"font-size: 11px; color: {COLORS['muted']};"
            "background-color: transparent; border: none;"
        )
        text_block.addWidget(lbl_title)
        text_block.addWidget(lbl_sub)
        header_row.addLayout(text_block, 1)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {COLORS['primary']};"
            f"background-color: {COLORS['primary_soft']}; border: 1px solid #BFDBFE;"
            "border-radius: 10px; padding: 2px 10px;"
        )
        self.lbl_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(self.lbl_count)
        layout.addLayout(header_row)

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

        # Ligne de champs
        form_row = QHBoxLayout()
        form_row.setSpacing(14)
        form_row.setAlignment(Qt.AlignBottom)

        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDisplayFormat("dd/MM/yyyy")
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setStyleSheet(DATE_STYLE)
        self.txt_date.setFixedWidth(140)
        self.txt_date.setFixedHeight(38)
        form_row.addLayout(_make_field_group("Date", self.txt_date))

        self.txt_vers_scol = QLineEdit("0")
        self.txt_vers_scol.setStyleSheet(INPUT_STYLE)
        self.txt_vers_scol.setFixedWidth(125)
        self.txt_vers_scol.setFixedHeight(38)
        self.txt_vers_scol.textChanged.connect(self._update_valider_button)
        form_row.addLayout(_make_field_group("Scolarité (F CFA)", self.txt_vers_scol))

        self.txt_vers_trans = QLineEdit("0")
        self.txt_vers_trans.setStyleSheet(INPUT_STYLE)
        self.txt_vers_trans.setFixedWidth(125)
        self.txt_vers_trans.setFixedHeight(38)
        self.txt_vers_trans.textChanged.connect(self._update_valider_button)
        # Transport désactivé pour la version collège CJGA — champ masqué,
        # la valeur interne reste "0" (aucune saisie possible).
        self.grp_vers_trans = QWidget()
        self.grp_vers_trans.setLayout(_make_field_group("Transport (F CFA)", self.txt_vers_trans))
        self.grp_vers_trans.setVisible(Config.ENABLE_TRANSPORT)
        form_row.addWidget(self.grp_vers_trans)

        self.txt_vers_cant = QLineEdit("0")
        self.txt_vers_cant.setStyleSheet(INPUT_STYLE)
        self.txt_vers_cant.setFixedWidth(125)
        self.txt_vers_cant.setFixedHeight(38)
        self.txt_vers_cant.textChanged.connect(self._update_valider_button)
        # Cantine désactivée pour la version collège CJGA — champ masqué,
        # la valeur interne reste "0" (aucune saisie possible).
        self.grp_vers_cant = QWidget()
        self.grp_vers_cant.setLayout(_make_field_group("Cantine (F CFA)", self.txt_vers_cant))
        self.grp_vers_cant.setVisible(Config.ENABLE_CANTINE)
        form_row.addWidget(self.grp_vers_cant)

        self.combo_mode_paiement = QComboBox()
        self.combo_mode_paiement.addItems(MODES_PAIEMENT)
        self.combo_mode_paiement.setStyleSheet(COMBO_STYLE)
        self.combo_mode_paiement.setFixedWidth(140)
        self.combo_mode_paiement.setFixedHeight(38)
        form_row.addLayout(_make_field_group("Mode de paiement", self.combo_mode_paiement))

        self.combo_titulaire = QComboBox()
        self.combo_titulaire.addItems(TITULAIRES_PAIEMENT)
        self.combo_titulaire.setStyleSheet(COMBO_STYLE)
        self.combo_titulaire.setFixedWidth(130)
        self.combo_titulaire.setFixedHeight(38)
        form_row.addLayout(_make_field_group("Titulaire", self.combo_titulaire))

        # Toggle Réduction
        reduc_vbox = QVBoxLayout()
        reduc_vbox.setSpacing(4)
        lbl_reduc = QLabel("RÉDUCTION")
        lbl_reduc.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #94A3B8;"
            "background-color: transparent; border: none; letter-spacing: 0.8px;"
        )
        self.toggle_reduction = ToggleSwitch()
        reduc_vbox.addWidget(lbl_reduc)
        reduc_vbox.addWidget(self.toggle_reduction)
        form_row.addLayout(reduc_vbox)

        form_row.addStretch()

        # Bouton Valider
        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(4)
        btn_vbox.setAlignment(Qt.AlignBottom)
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
                min-height: 38px;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{ background-color: #15803D; }}
            QPushButton:pressed {{ background-color: #166534; }}
            QPushButton:disabled {{ background-color: #E5E7EB; color: #9CA3AF; }}
        """)
        self.btn_valider_versement.setMinimumWidth(170)
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
        self.table_history.setColumnCount(6)
        self.table_history.setHorizontalHeaderLabels([
            "Date", "Scolarité", "Transport", "Cantine", "Réduc.", "ID"
        ])
        if not Config.ENABLE_TRANSPORT:
            self.table_history.setColumnHidden(2, True)
        if not Config.ENABLE_CANTINE:
            self.table_history.setColumnHidden(3, True)
        self.table_history.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_history.setSelectionMode(QTableWidget.SingleSelection)
        self.table_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setStyleSheet(TABLE_STYLE + "QTableWidget { border: none; }")
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.horizontalHeader().setHighlightSections(False)
        self.table_history.setColumnHidden(5, True)
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
        self.fs_scol  = FinancialSection("Scolarité",  COLORS["primary"])
        self.fs_trans = FinancialSection("Transport",   "#0369A1")
        self.fs_cant  = FinancialSection("Cantine",     COLORS["warning"])

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

        self.fs_trans.setVisible(False)
        self.fs_cant.setVisible(False)

        body_layout.addWidget(self.fs_scol)
        body_layout.addWidget(self.fs_trans)
        body_layout.addWidget(self.fs_cant)

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
        count = len(items)
        self.lbl_count.setText(f"{count} élève{'s' if count > 1 else ''}")

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

        self.load_history()

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

        total_due  = fin["scol_due"]  + fin["trans_due"]  + fin["cant_due"]
        total_paye = fin["scol_paye"] + fin["trans_paye"] + fin["cant_paye"]
        total_rem  = fin["scol_reste"] + fin["trans_reste"] + fin["cant_reste"]

        self.row_tot_due.set_value(fmt(total_due))
        self.row_tot_paid.set_value(fmt(total_paye))
        self.row_tot_reduc.setVisible(fin["total_reduc"] > 0)
        self.row_tot_reduc.set_value(fmt(fin["total_reduc"]))
        self.row_tot_rem.set_value(fmt(total_rem))

        try:
            color = COLORS["danger"] if total_rem > 0 else COLORS["success"]
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
            trans  = int(v.MontantVersTrans)
            cant   = int(v.MontantCantine)
            vals = [
                dt_str,
                f"{scol:,} F".replace(",", " "),
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
                    if trans > 0:
                        item.setForeground(QColor("#0369A1"))
                elif col == 3:
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
            m_scol  = _parse_input(self.txt_vers_scol.text())
            m_trans = _parse_input(self.txt_vers_trans.text())
            m_cant  = _parse_input(self.txt_vers_cant.text())
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Un des montants saisis est incorrect.")
            return

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
            m_autres=0,
            reduction=reduction_active,
            impaye=False,
            restitution=False,
            login=AppSession.get_logged_in_username()
        )
        if success:
            self.toggle_reduction.setChecked(False)
            self.combo_titulaire.setCurrentIndex(0)
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
                "motif":         _compute_motif(m_scol, m_trans, m_cant),
                "mode_paiement": self.combo_mode_paiement.currentText(),
                "titulaire":     self.combo_titulaire.currentText(),
                "total_recu":    m_scol + m_trans + m_cant,
                # SCOLARITE
                "scol_active": fin_before["options"]["scolarite"],
                "scol_due":    fin_before["scol_reste"],   # solde dû AVANT ce paiement
                "scol_recu":   m_scol,
                "scol_reste":  fin_after["scol_reste"],
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

    def _update_valider_button(self):
        try:
            total = 0
            if self.txt_vers_scol.isEnabled():
                total += _parse_input(self.txt_vers_scol.text())
            if self.txt_vers_trans.isEnabled():
                total += _parse_input(self.txt_vers_trans.text())
            if self.txt_vers_cant.isEnabled():
                total += _parse_input(self.txt_vers_cant.text())
        except Exception:
            total = 0
        self.btn_valider_versement.setEnabled(total > 0)

    def clear_fields(self):
        self.txt_vers_scol.setText("")
        self.txt_vers_trans.setText("")
        self.txt_vers_cant.setText("")
        self.table_history.setRowCount(0)

    def clear_financial_panel(self):
        self.lbl_fin_eleve.setText("—")
        for row in [
            self.row_sc_due,  self.row_sc_paid,  self.row_sc_rem,
            self.row_tr_due,  self.row_tr_paid,  self.row_tr_rem,
            self.row_ca_due,  self.row_ca_paid,  self.row_ca_rem,
            self.row_tot_due, self.row_tot_paid, self.row_tot_rem,
        ]:
            row.set_value("0 F")
        self.row_sc_reduc.setVisible(False)
        self.row_tot_reduc.setVisible(False)
        self.fs_trans.setVisible(False)
        self.fs_cant.setVisible(False)
