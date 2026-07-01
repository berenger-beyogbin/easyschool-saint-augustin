import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QDateEdit, QComboBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QDate
from services.compte_service import CompteService
from services.comptabilite_service import ComptabiliteService
from app.session import AppSession
from app.styles import (
    COLORS, INPUT_STYLE, COMBO_STYLE, DATE_STYLE, FIELD_LABEL_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY,
    apply_table_style, configure_table_action_button, make_table_action_container
)


class EnregistrementMouvementView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.comptes_list = []
        self.init_ui()
        self.load_comptes()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # ── CARTE FORMULAIRE ─────────────────────────────────────────────────
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet(f"""
            QFrame#formCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-top: 3px solid {COLORS['primary']};
                border-radius: 10px;
            }}
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 14, 20, 16)
        form_layout.setSpacing(14)

        lbl_form_title = QLabel("  Enregistrement de Mouvement Financier")
        lbl_form_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['primary_dark']};"
            "background-color: transparent; border: none; padding-bottom: 2px;"
        )
        form_layout.addWidget(lbl_form_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; border: none; max-height: 1px;")
        form_layout.addWidget(sep)

        # Ligne 1 : Date | Bénéficiaire | Téléphone
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        col_date = QVBoxLayout()
        col_date.setSpacing(4)
        col_date.addWidget(self._lbl("Date du Mouvement *"))
        self.txt_date = QDateEdit()
        self.txt_date.setDisplayFormat("dd/MM/yyyy")
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setStyleSheet(DATE_STYLE)
        self.txt_date.setCursor(Qt.CursorShape.PointingHandCursor)
        col_date.addWidget(self.txt_date)
        row1.addLayout(col_date, 1)

        col_benef = QVBoxLayout()
        col_benef.setSpacing(4)
        col_benef.addWidget(self._lbl("Bénéficiaire *"))
        self.txt_benef = QLineEdit()
        self.txt_benef.setPlaceholderText("Nom du bénéficiaire…")
        self.txt_benef.setStyleSheet(INPUT_STYLE)
        col_benef.addWidget(self.txt_benef)
        row1.addLayout(col_benef, 2)

        col_tel = QVBoxLayout()
        col_tel.setSpacing(4)
        col_tel.addWidget(self._lbl("Tél. Bénéficiaire"))
        self.txt_tel = QLineEdit()
        self.txt_tel.setPlaceholderText("Numéro de contact…")
        self.txt_tel.setStyleSheet(INPUT_STYLE)
        col_tel.addWidget(self.txt_tel)
        row1.addLayout(col_tel, 1)

        form_layout.addLayout(row1)

        # Ligne 2 : Compte | Type de mouvement | Montant
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        col_compte = QVBoxLayout()
        col_compte.setSpacing(4)
        col_compte.addWidget(self._lbl("Compte *"))
        self.combo_compte = QComboBox()
        self.combo_compte.setStyleSheet(COMBO_STYLE)
        col_compte.addWidget(self.combo_compte)
        row2.addLayout(col_compte, 2)

        col_sens = QVBoxLayout()
        col_sens.setSpacing(4)
        col_sens.addWidget(self._lbl("Type de Mouvement *"))
        self.combo_sens = QComboBox()
        self.combo_sens.setStyleSheet(COMBO_STYLE)
        self.combo_sens.addItem("Débit (Sortie d'argent)", "Debit")
        self.combo_sens.addItem("Crédit (Entrée d'argent)", "Credit")
        col_sens.addWidget(self.combo_sens)
        row2.addLayout(col_sens, 1)

        col_montant = QVBoxLayout()
        col_montant.setSpacing(4)
        col_montant.addWidget(self._lbl("Montant (FCFA) *"))
        self.txt_montant = QLineEdit()
        self.txt_montant.setPlaceholderText("Ex : 25 000")
        self.txt_montant.setStyleSheet(INPUT_STYLE)
        col_montant.addWidget(self.txt_montant)
        row2.addLayout(col_montant, 1)

        form_layout.addLayout(row2)

        # Ligne 3 : Détail pleine largeur
        col_detail = QVBoxLayout()
        col_detail.setSpacing(4)
        col_detail.addWidget(self._lbl("Détail / Motif"))
        self.txt_detail = QLineEdit()
        self.txt_detail.setPlaceholderText("Détails complémentaires sur le mouvement financier…")
        self.txt_detail.setStyleSheet(INPUT_STYLE)
        col_detail.addWidget(self.txt_detail)
        form_layout.addLayout(col_detail)

        # Boutons
        row_btn = QHBoxLayout()
        row_btn.addStretch()
        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.setMinimumWidth(130)
        self.btn_valider.setFixedHeight(38)
        self.btn_valider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_valider.clicked.connect(self.save_mouvement)

        self.btn_annuler = QPushButton("✕  Annuler")
        self.btn_annuler.setStyleSheet(BUTTON_SECONDARY)
        self.btn_annuler.setMinimumWidth(110)
        self.btn_annuler.setFixedHeight(38)
        self.btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_annuler.clicked.connect(self.clear_form)

        row_btn.addWidget(self.btn_valider)
        row_btn.addWidget(self.btn_annuler)
        form_layout.addLayout(row_btn)

        layout.addWidget(form_card)

        # ── CARTE TABLEAU ─────────────────────────────────────────────────────
        table_card = QFrame()
        table_card.setObjectName("tableCard")
        table_card.setStyleSheet(f"""
            QFrame#tableCard {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 12, 16, 14)
        table_layout.setSpacing(10)

        # En-tête tableau
        hdr = QHBoxLayout()
        lbl_table_title = QLabel("Mouvements de l'Année Scolaire Active")
        lbl_table_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {COLORS['text_soft']};"
            "background-color: transparent; border: none;"
        )
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"font-size: 11px; color: {COLORS['muted']}; background-color: {COLORS['border_soft']};"
            f"border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 2px 10px;"
        )
        hdr.addWidget(lbl_table_title)
        hdr.addStretch()
        hdr.addWidget(self.lbl_count)
        table_layout.addLayout(hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Date", "Bénéficiaire", "Compte", "Montant", "Sens", "Action"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 90)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        apply_table_style(self.table)
        table_layout.addWidget(self.table)

        layout.addWidget(table_card, 1)

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _lbl(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(FIELD_LABEL_STYLE)
        return lbl

    @staticmethod
    def _make_sens_badge(sens_code: str) -> QWidget:
        """Retourne un conteneur centré avec un badge coloré DÉBIT / CRÉDIT."""
        is_debit = sens_code == "Debit"
        text   = "DÉBIT"   if is_debit else "CRÉDIT"
        fg     = COLORS["danger"]   if is_debit else COLORS["success"]
        bg     = "#FEE2E2"          if is_debit else "#DCFCE7"
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {fg}; background-color: {bg}; font-size: 11px; font-weight: bold;"
            "border-radius: 10px; padding: 2px 10px; border: none;"
        )
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(container)
        h.setContentsMargins(6, 4, 6, 4)
        h.addWidget(lbl)
        return container

    # ── données ───────────────────────────────────────────────────────────────
    def load_comptes(self):
        self.combo_compte.clear()
        self.comptes_list = CompteService.get_all_comptes()
        self.combo_compte.addItem("--- Sélectionner un compte ---", None)
        for c in self.comptes_list:
            self.combo_compte.addItem(f"{c.NumCompte} - {c.LibCompte}", c.IDCompte)

    def load_data(self):
        self.table.setRowCount(0)
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            self.lbl_count.setText("0 enregistrement")
            return

        mouvements = ComptabiliteService.get_all_mouvements(active_annee_id)
        nb = len(mouvements)
        self.lbl_count.setText(f"{nb} enregistrement{'s' if nb > 1 else ''}")

        for i, item in enumerate(mouvements):
            self.table.insertRow(i)

            date_str    = item.DateSortie.strftime("%d/%m/%Y") if item.DateSortie else ""
            compte_str  = (
                f"{item.compte.NumCompte} - {item.compte.LibCompte}"
                if item.compte else str(item.IDCompte)
            )

            item_code    = QTableWidgetItem(item.CodeSortie or f"SF-{item.IDSortieFin}")
            item_date    = QTableWidgetItem(date_str)
            item_benef   = QTableWidgetItem(item.Benef)
            item_compte  = QTableWidgetItem(compte_str)
            item_montant = QTableWidgetItem(self.format_fcfa(item.Montant))
            item_montant.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(i, 0, item_code)
            self.table.setItem(i, 1, item_date)
            self.table.setItem(i, 2, item_benef)
            self.table.setItem(i, 3, item_compte)
            self.table.setItem(i, 4, item_montant)

            # Badge Sens
            self.table.setCellWidget(i, 5, self._make_sens_badge(item.DebitCredit))

            # Bouton suppression
            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(
                lambda checked=False, id_s=item.IDSortieFin, c=item.CodeSortie:
                self.delete_mouvement(id_s, c)
            )
            self.table.setCellWidget(i, 6, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    # ── actions ───────────────────────────────────────────────────────────────
    def save_mouvement(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            QMessageBox.warning(self, "Erreur d'année", "Veuillez sélectionner une année scolaire active !")
            return

        date_val   = self.txt_date.date().toPython()
        benef      = self.txt_benef.text().strip()
        tel        = self.txt_tel.text().strip()
        compte_id  = self.combo_compte.currentData()
        sens       = self.combo_sens.currentData()
        montant_str = self.txt_montant.text().strip()
        detail     = self.txt_detail.text().strip()

        if not benef:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le nom du bénéficiaire !")
            return
        if not compte_id:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez associer un compte comptable au mouvement !")
            return
        if not montant_str:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le montant !")
            return

        try:
            montant = float(montant_str.replace(" ", "").replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Erreur de format", "Veuillez saisir un montant numérique valide !")
            return

        success, msg = ComptabiliteService.create_mouvement(
            benef=benef,
            montant=montant,
            date_sortie=date_val,
            id_compte=compte_id,
            debit_credit=sens,
            detail=detail,
            num_benef=tel
        )

        if success:
            QMessageBox.information(self, "Mouvement enregistré", msg)
            self.clear_form()
            self.load_data()
        else:
            QMessageBox.critical(self, "Erreur d'enregistrement", msg)

    def delete_mouvement(self, id_mouv, code_mouv):
        ans = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous supprimer le mouvement {code_mouv or ''} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            success, msg = ComptabiliteService.delete_mouvement(id_mouv)
            if success:
                QMessageBox.information(self, "Succès", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur", msg)

    def clear_form(self):
        self.txt_benef.clear()
        self.txt_tel.clear()
        self.txt_montant.clear()
        self.txt_detail.clear()
        self.combo_compte.setCurrentIndex(0)
        self.combo_sens.setCurrentIndex(0)
        self.txt_date.setDate(QDate.currentDate())

    @staticmethod
    def format_fcfa(montant) -> str:
        try:
            val = int(float(montant))
            return f"{val:,}".replace(",", " ") + " FCFA"
        except Exception:
            return f"{montant} FCFA"
