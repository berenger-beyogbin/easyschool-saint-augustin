from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit,
    QAbstractItemView
)
from PySide6.QtCore import QDate, Qt

from services.frais_examen_cm2_service import FraisExamenCM2Service
from app.session import AppSession
from utils.receipt_printer import ReceiptPrinter
from app.styles import (
    COLORS, INPUT_STYLE, DATE_STYLE, BUTTON_SUCCESS,
    BUTTON_SECONDARY, BUTTON_DANGER, TABLE_STYLE, apply_card_shadow
)
from views.ui_components import FinancialSection, show_confirm, show_error, show_success


def _fmt_input(v) -> str:
    """Formate un montant entier avec séparateur de milliers (espace)."""
    try:
        return f"{int(float(v)):,}".replace(",", " ")
    except Exception:
        return "0"


def _parse_input(text: str) -> float:
    """Parse un montant saisi (supporte les espaces comme séparateurs de milliers)."""
    return float(text.replace(" ", "").replace(",", "").strip() or 0)


def _make_field_group(label_text: str, widget) -> QVBoxLayout:
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
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
        }}
    """)
    apply_card_shadow(card)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(12)
    return card, layout


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


class ExamenCM2View(QWidget):
    """Encaissement du frais d'examen CM2 — montant configurable, paye en une
    seule fois par eleve, ecran independant de la Caisse Scolarite."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.selected_eleve_id = None
        self.selected_famille_id = None
        self.selected_eleve_row = None
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self._build_montant_panel(layout)
        self._build_liste_panel(layout)
        self._build_encaissement_panel(layout)

        self.load_data()

    # -------------------------------------------------------------------------
    # PANNEAU MONTANT CONFIGURÉ
    # -------------------------------------------------------------------------

    def _build_montant_panel(self, parent_layout):
        panel, layout = _make_panel(COLORS['primary'])
        row = QHBoxLayout()
        row.setSpacing(14)
        row.setAlignment(Qt.AlignVCenter)

        lbl_t = QLabel("Montant du frais d'examen CM2 (année active)")
        lbl_t.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        row.addWidget(lbl_t, 1)

        self.txt_montant = QLineEdit("0")
        self.txt_montant.setStyleSheet(INPUT_STYLE)
        self.txt_montant.setFixedWidth(130)
        self.txt_montant.setFixedHeight(36)
        row.addWidget(self.txt_montant)

        self.btn_save_montant = QPushButton("Enregistrer")
        self.btn_save_montant.setStyleSheet(BUTTON_SECONDARY)
        self.btn_save_montant.setFixedHeight(36)
        self.btn_save_montant.setCursor(Qt.PointingHandCursor)
        self.btn_save_montant.clicked.connect(self.on_save_montant)
        row.addWidget(self.btn_save_montant)

        layout.addLayout(row)
        parent_layout.addWidget(panel)

    def on_save_montant(self):
        active_annee_id = AppSession.get_active_annee_id()
        try:
            montant = _parse_input(self.txt_montant.text())
        except ValueError:
            show_error(self, "Erreur", "Montant saisi incorrect.")
            return
        success, msg = FraisExamenCM2Service.save_montant(active_annee_id, montant)
        if success:
            show_success(self, "Succès", msg)
            self.load_data()
        else:
            show_error(self, "Erreur", msg)

    # -------------------------------------------------------------------------
    # PANNEAU LISTE DES ÉLÈVES DE CM2
    # -------------------------------------------------------------------------

    def _build_liste_panel(self, parent_layout):
        panel, layout = _make_panel(COLORS['primary'])

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)
        lbl_title = QLabel("Élèves inscrits en CM2")
        lbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        lbl_sub = QLabel("Cliquez sur une ligne pour encaisser ou consulter le paiement")
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
        self.btn_refresh.clicked.connect(self.load_data)
        search_row.addWidget(self.btn_refresh, 0, Qt.AlignVCenter)
        layout.addLayout(search_row)

        self.table_eleves = QTableWidget()
        self.table_eleves.setColumnCount(4)
        self.table_eleves.setHorizontalHeaderLabels([
            "Matricule", "Nom & Prénoms", "Classe", "Statut"
        ])
        self.table_eleves.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_eleves.setSelectionMode(QTableWidget.SingleSelection)
        self.table_eleves.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_eleves.setAlternatingRowColors(True)
        self.table_eleves.setStyleSheet(TABLE_STYLE)
        self.table_eleves.verticalHeader().setVisible(False)
        self.table_eleves.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_eleves.horizontalHeader().setHighlightSections(False)
        self.table_eleves.setFixedHeight(280)
        self.table_eleves.setFrameShape(QFrame.NoFrame)
        self.table_eleves.setShowGrid(False)
        self.table_eleves.itemSelectionChanged.connect(self.on_eleve_selected)
        layout.addWidget(self.table_eleves)

        parent_layout.addWidget(panel, 1)

    # -------------------------------------------------------------------------
    # PANNEAU ENCAISSEMENT
    # -------------------------------------------------------------------------

    def _build_encaissement_panel(self, parent_layout):
        self.panel_encaissement, layout = _make_panel(COLORS['success'])
        self.panel_encaissement.setEnabled(False)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(12)

        lbl_t = QLabel("Encaisser le frais d'examen CM2")
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

        self.fs_examen = FinancialSection("Situation", COLORS["primary"])
        self.row_due = self.fs_examen.add_row("Montant dû", "0 F")
        self.row_paid = self.fs_examen.add_row("Montant réglé", "0 F", COLORS["success"])
        self.row_rem = self.fs_examen.add_row("Reste", "0 F", COLORS["danger"], bold=True)
        layout.addWidget(self.fs_examen)

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

        self.txt_montant_verse = QLineEdit("0")
        self.txt_montant_verse.setStyleSheet(INPUT_STYLE)
        self.txt_montant_verse.setFixedWidth(140)
        self.txt_montant_verse.setFixedHeight(38)
        form_row.addLayout(_make_field_group("Montant encaissé (F CFA)", self.txt_montant_verse))

        form_row.addStretch()

        self.btn_encaisser = QPushButton("✓  Encaisser et imprimer le reçu")
        self.btn_encaisser.setStyleSheet(BUTTON_SUCCESS)
        self.btn_encaisser.setFixedHeight(38)
        self.btn_encaisser.setCursor(Qt.PointingHandCursor)
        self.btn_encaisser.clicked.connect(self.on_encaisser)
        form_row.addWidget(self.btn_encaisser)

        self.btn_annuler = QPushButton("Annuler l'encaissement")
        self.btn_annuler.setStyleSheet(BUTTON_DANGER)
        self.btn_annuler.setFixedHeight(38)
        self.btn_annuler.setCursor(Qt.PointingHandCursor)
        self.btn_annuler.clicked.connect(self.on_annuler)
        self.btn_annuler.setVisible(False)
        form_row.addWidget(self.btn_annuler)

        layout.addLayout(form_row)
        parent_layout.addWidget(self.panel_encaissement)

    # =========================================================================
    # LOGIQUE MÉTIER
    # =========================================================================

    def load_data(self):
        active_annee_id = AppSession.get_active_annee_id()
        self.txt_montant.setText(
            _fmt_input(FraisExamenCM2Service.get_montant_configure(active_annee_id))
        )
        self._eleves_cache = FraisExamenCM2Service.get_eleves_cm2(active_annee_id)
        self.display_eleves(self._eleves_cache)

    def on_search_changed(self):
        query = self.txt_recherche.text().strip().lower()
        if not query:
            self.display_eleves(self._eleves_cache)
            return
        filtered = [
            e for e in self._eleves_cache
            if query in e["matricule"].lower() or query in e["nom"].lower()
        ]
        self.display_eleves(filtered)

    def display_eleves(self, items):
        self.table_eleves.setRowCount(len(items))
        count = len(items)
        self.lbl_count.setText(f"{count} élève{'s' if count > 1 else ''}")

        for i, e in enumerate(items):
            statut = "Payé" if e["paye"] else "Impayé"
            vals = [e["matricule"], e["nom"], e["classe"], statut]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.UserRole, e)
                if col == 3:
                    item.setForeground(
                        Qt.GlobalColor.darkGreen if e["paye"] else Qt.GlobalColor.darkRed
                    )
                self.table_eleves.setItem(i, col, item)
            self.table_eleves.setRowHeight(i, 34)

        # clearSelection() est indispensable : sans elle, la ligne selectionnee
        # avant un rechargement reste "selectionnee" au niveau du modele Qt meme
        # si ses donnees ont change, et une re-selection de la meme ligne ne
        # declenche alors plus itemSelectionChanged (les infos affichees restent
        # perimees, ex. apres un encaissement qui vient de solder l'eleve).
        self.table_eleves.clearSelection()
        self.selected_eleve_id = None
        self.selected_famille_id = None
        self.selected_eleve_row = None
        self.panel_encaissement.setEnabled(False)
        self.lbl_target_student.setText("Aucun élève sélectionné")
        self.lbl_target_student.setStyleSheet(_CHIP_MUTED)

    def on_eleve_selected(self):
        selected_ranges = self.table_eleves.selectedRanges()
        if not selected_ranges:
            return
        row = selected_ranges[0].topRow()
        item_mat = self.table_eleves.item(row, 0)
        item_nom = self.table_eleves.item(row, 1)
        if not item_mat or not item_nom:
            return
        eleve_data = item_mat.data(Qt.UserRole)
        self.selected_eleve_row = eleve_data
        self.selected_eleve_id = eleve_data["id_eleve"]
        self.selected_famille_id = eleve_data["id_famille"]
        self.lbl_target_student.setText(f"{item_nom.text()}  ·  {item_mat.text()}")
        self.lbl_target_student.setStyleSheet(_CHIP_SUCCESS)
        self.panel_encaissement.setEnabled(True)
        self.refresh_situation()

    def refresh_situation(self):
        montant_du = _parse_input(self.txt_montant.text())
        e = self.selected_eleve_row
        montant_regle = e["montant_paye"] if e else 0.0
        reste = max(0.0, montant_du - montant_regle)

        self.row_due.set_value(f"{_fmt_input(montant_du)} F")
        self.row_paid.set_value(f"{_fmt_input(montant_regle)} F")
        self.row_rem.set_value(f"{_fmt_input(reste)} F")

        deja_paye = bool(e and e["paye"])
        self.txt_montant_verse.setEnabled(not deja_paye)
        self.txt_montant_verse.setText("0" if not deja_paye else _fmt_input(montant_regle))
        self.btn_encaisser.setVisible(not deja_paye)
        self.btn_annuler.setVisible(deja_paye)

    def on_encaisser(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_eleve_id or not self.selected_famille_id:
            show_error(self, "Erreur", "Sélecteur d'élève manquant.")
            return
        try:
            montant = _parse_input(self.txt_montant_verse.text())
        except ValueError:
            show_error(self, "Erreur", "Le montant saisi est incorrect.")
            return

        montant_du = _parse_input(self.txt_montant.text())
        success, msg, new_id = FraisExamenCM2Service.create_versement(
            id_annee=active_annee_id,
            id_eleve=self.selected_eleve_id,
            id_famille=self.selected_famille_id,
            date_v=self.txt_date.date().toPython(),
            montant=montant,
            login=AppSession.get_logged_in_username(),
        )
        if not success:
            show_error(self, "Erreur", msg)
            return

        reste_apres = max(0.0, montant_du - montant)
        receipt_data = {
            "date": self.txt_date.date().toString("dd/MM/yyyy"),
            "matricule": self.selected_eleve_row["matricule"],
            "nom": self.selected_eleve_row["nom"],
            "classe": self.selected_eleve_row["classe"],
            "numero": str(new_id) if new_id else "—",
            "examen_due": montant_du,
            "examen_recu": montant,
            "examen_reste": reste_apres,
        }

        self.load_data()
        ReceiptPrinter.print_receipt_examen_cm2(self, receipt_data)

    def on_annuler(self):
        e = self.selected_eleve_row
        if not e or not e["id_versement"]:
            return
        if not show_confirm(
            self, "Confirmation",
            f"Annuler l'encaissement du frais d'examen CM2 pour {e['nom']} ?"
        ):
            return
        success, msg = FraisExamenCM2Service.delete_versement(e["id_versement"])
        if success:
            show_success(self, "Succès", msg)
            self.load_data()
        else:
            show_error(self, "Erreur", msg)
