from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt
from services.niveau_service import NiveauService
from services.montant_cantine_service import MontantCantineService
from app.session import AppSession
from app.styles import (
    COLORS, INPUT_STYLE, SECTION_TITLE_STYLE,
    BUTTON_PRIMARY, GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE,
    apply_table_style
)


class MontantCantineView(QWidget):
    """Vue permettant de paramétrer les coûts de restauration (Cantine) par niveau."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(20)

        # ---------------- CÔTÉ GAUCHE ----------------
        pane_gauche = QWidget()
        layout_gauche = QVBoxLayout(pane_gauche)
        layout_gauche.setContentsMargins(0, 0, 0, 0)
        layout_gauche.setSpacing(15)

        group_commun = QGroupBox("APPLICATION COMMUNE À TOUS LES NIVEAUX")
        group_commun.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        layout_commun = QVBoxLayout(group_commun)
        layout_commun.setSpacing(10)

        lbl_com_info = QLabel("Saisissez un coût cantine par défaut pour tous :")
        lbl_com_info.setWordWrap(True)
        lbl_com_info.setStyleSheet(
            f"color: {COLORS['muted']}; font-style: italic; font-size: 11px; background-color: transparent;"
        )
        layout_commun.addWidget(lbl_com_info)

        layout_commun.addWidget(QLabel("Tarif Cantine commun (F CFA) :"))
        self.txt_com_montant = QLineEdit("0")
        self.txt_com_montant.setStyleSheet(INPUT_STYLE)
        layout_commun.addWidget(self.txt_com_montant)

        btn_appliquer_tout = QPushButton("Appliquer à tous les niveaux")
        btn_appliquer_tout.setStyleSheet(BUTTON_PRIMARY)
        btn_appliquer_tout.clicked.connect(self.on_apply_common)
        layout_commun.addWidget(btn_appliquer_tout)

        layout_gauche.addWidget(group_commun)

        self.group_individuel = QGroupBox("MODIFIER LE NIVEAU SÉLECTIONNÉ")
        self.group_individuel.setStyleSheet(GROUPBOX_STYLE)
        layout_indiv = QVBoxLayout(self.group_individuel)
        layout_indiv.setSpacing(10)

        self.lbl_selected_niveau = QLabel("Aucun niveau sélectionné")
        self.lbl_selected_niveau.setStyleSheet(
            f"font-weight: bold; color: {COLORS['text']}; font-size: 12px; background-color: transparent;"
        )
        layout_indiv.addWidget(self.lbl_selected_niveau)

        layout_indiv.addWidget(QLabel("Frais de cantine (F CFA) :"))
        self.txt_ind_montant = QLineEdit("0")
        self.txt_ind_montant.setStyleSheet(INPUT_STYLE)
        layout_indiv.addWidget(self.txt_ind_montant)

        self.btn_enregistrer_niveau = QPushButton("✓  Enregistrer ce niveau")
        self.btn_enregistrer_niveau.setStyleSheet(BUTTON_PRIMARY)
        self.btn_enregistrer_niveau.setEnabled(False)
        self.btn_enregistrer_niveau.clicked.connect(self.on_save_individual)
        layout_indiv.addWidget(self.btn_enregistrer_niveau)

        layout_gauche.addWidget(self.group_individuel)
        layout_gauche.addStretch()

        layout_principal.addWidget(pane_gauche, 1)

        # ---------------- CÔTÉ DROIT ----------------
        pane_droit = QWidget()
        layout_droit = QVBoxLayout(pane_droit)
        layout_droit.setContentsMargins(0, 0, 0, 0)
        layout_droit.setSpacing(10)

        lbl_titre_table = QLabel("Frais de Cantine (Restauration) par Niveau")
        lbl_titre_table.setStyleSheet(SECTION_TITLE_STYLE)
        layout_droit.addWidget(lbl_titre_table)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Niveau", "Frais de Cantine"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout_droit.addWidget(self.table)

        layout_principal.addWidget(pane_droit, 2)

        self.selected_niveau_id = None
        self.load_montants()

    def load_montants(self):
        """Charge la grille avec les coûts de cantine configurés."""
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        niveaux = NiveauService.get_all_with_cycle()
        tarifs = MontantCantineService.get_montants_by_annee(active_annee_id)
        tarifs_dict = {t.IDNiveau: t for t in tarifs}

        self.table.setRowCount(len(niveaux))
        for i, niv in enumerate(niveaux):
            nid = niv["IDT_Niveau"]
            lib_niv = niv["Libelle"]

            m_cant = 0.0
            if nid in tarifs_dict:
                m_cant = float(tarifs_dict[nid].Montant)

            item_niv = QTableWidgetItem(lib_niv)
            item_niv.setData(Qt.UserRole, nid)
            item_niv.setFlags(item_niv.flags() & ~Qt.ItemIsEditable)

            item_m = QTableWidgetItem(f"{int(m_cant):,} F")
            item_m.setFlags(item_m.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(i, 0, item_niv)
            self.table.setItem(i, 1, item_m)

        self.lbl_selected_niveau.setText("Aucun niveau sélectionné")
        self.btn_enregistrer_niveau.setEnabled(False)
        self.selected_niveau_id = None

    def on_row_selected(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        row = selected_ranges[0].topRow()
        item_niv = self.table.item(row, 0)
        if not item_niv:
            return

        self.selected_niveau_id = item_niv.data(Qt.UserRole)
        self.lbl_selected_niveau.setText(f"Niveau : {item_niv.text()}")
        self.btn_enregistrer_niveau.setEnabled(True)

        m_cant = self.clean_amount(self.table.item(row, 1).text())
        self.txt_ind_montant.setText(str(m_cant))

    def clean_amount(self, txt: str) -> int:
        return int("".join(c for c in txt if c.isdigit()))

    def on_apply_common(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id:
            return

        try:
            val_com = float(self.txt_com_montant.text().strip() or 0)
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Saisie numerique invalide.")
            return

        success, msg = MontantCantineService.apply_common_amount_to_all_levels(active_annee_id, val_com)
        if success:
            QMessageBox.information(self, "Succes", "Les tarifs de cantine ont bien été propagés !")
            self.load_montants()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def on_save_individual(self):
        active_annee_id = AppSession.get_active_annee_id()
        if not active_annee_id or not self.selected_niveau_id:
            return

        try:
            val = float(self.txt_ind_montant.text().strip() or 0)
        except ValueError:
            QMessageBox.critical(self, "Erreur", "Saisie numerique invalide.")
            return

        success, msg = MontantCantineService.save_montant_cantine(
            active_annee_id, self.selected_niveau_id, val
        )
        if success:
            QMessageBox.information(self, "Succes", "Le coût de cantine pour ce niveau a bien ete enregistre.")
            self.load_montants()
        else:
            QMessageBox.critical(self, "Erreur", msg)
