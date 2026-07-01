from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from services.compte_service import CompteService
from app.styles import (
    COLORS, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_DANGER,
    GROUPBOX_ACCENT_STYLE, GROUPBOX_STYLE, apply_table_style,
    configure_table_action_button, make_table_action_container
)

class CompteView(QWidget):
    """
    Vue pour la création et la gestion des Comptes de comptabilité.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # Layout principal vertical
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Groupe de Formulaire de Saisie
        group_form = QGroupBox("Nouveau Compte")
        group_form.setStyleSheet(GROUPBOX_ACCENT_STYLE)
        form_layout = QVBoxLayout(group_form)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        # Ligne de Saisie
        row_inputs = QHBoxLayout()
        row_inputs.setSpacing(15)

        # Champ Numéro Compte
        lbl_num = QLabel("N° Compte *:")
        lbl_num.setStyleSheet(f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;")
        self.txt_num = QLineEdit()
        self.txt_num.setPlaceholderText("Ex: 601")
        self.txt_num.setStyleSheet(INPUT_STYLE)
        row_inputs.addWidget(lbl_num)
        row_inputs.addWidget(self.txt_num, 1)

        # Champ Libellé du Compte
        lbl_lib = QLabel("Libellé du Compte *:")
        lbl_lib.setStyleSheet(f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;")
        self.txt_lib = QLineEdit()
        self.txt_lib.setPlaceholderText("Ex: Fournitures scolaires")
        self.txt_lib.setStyleSheet(INPUT_STYLE)
        row_inputs.addWidget(lbl_lib)
        row_inputs.addWidget(self.txt_lib, 2)

        form_layout.addLayout(row_inputs)

        # Ligne de Boutons
        row_buttons = QHBoxLayout()
        row_buttons.addStretch()

        self.btn_valider = QPushButton("Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_compte)
        row_buttons.addWidget(self.btn_valider)

        self.btn_annuler = QPushButton("Annuler")
        self.btn_annuler.setStyleSheet(BUTTON_SECONDARY)
        self.btn_annuler.clicked.connect(self.clear_form)
        row_buttons.addWidget(self.btn_annuler)

        form_layout.addLayout(row_buttons)
        layout.addWidget(group_form)

        # Partie Liste des Comptes
        group_list = QGroupBox("Liste des Comptes")
        group_list.setStyleSheet(GROUPBOX_STYLE)
        list_layout = QVBoxLayout(group_list)
        list_layout.setContentsMargins(15, 15, 15, 15)

        # Barre de recherche simple
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        lbl_search = QLabel("Rechercher :")
        lbl_search.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"
        )
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Saisir un numéro ou libellé de compte...")
        self.txt_search.setStyleSheet(INPUT_STYLE)
        self.txt_search.textChanged.connect(self.load_data)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.txt_search, 1)
        list_layout.addLayout(search_layout)
        list_layout.addSpacing(10)

        # Tableau des Comptes
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["N° Compte", "Libellé du Compte", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        apply_table_style(self.table)
        list_layout.addWidget(self.table)
        layout.addWidget(group_list, 1)

    def load_data(self):
        self.table.setRowCount(0)
        search_text = self.txt_search.text().strip()
        
        if search_text:
            lst = CompteService.search_comptes(search_text)
        else:
            lst = CompteService.get_all_comptes()

        for i, item in enumerate(lst):
            self.table.insertRow(i)
            
            # Création des QTableWidgetItem
            item_num = QTableWidgetItem(item.NumCompte)
            item_lib = QTableWidgetItem(item.LibCompte)
            
            item_num.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item_lib.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            self.table.setItem(i, 0, item_num)
            self.table.setItem(i, 1, item_lib)

            btn_suppr = QPushButton("Supprimer")
            configure_table_action_button(btn_suppr, "danger")
            btn_suppr.clicked.connect(lambda checked=False, id_c=item.IDCompte, num=item.NumCompte: self.delete_compte(id_c, num))
            self.table.setCellWidget(i, 2, make_table_action_container(btn_suppr))
            self.table.setRowHeight(i, 44)

    def save_compte(self):
        num = self.txt_num.text().strip()
        lib = self.txt_lib.text().strip()

        if not num:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le numéro de compte !")
            return
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir le libellé du compte !")
            return

        success, msg = CompteService.create_compte(num, lib)
        if success:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.clear_form()
            self.load_data()
        else:
            QMessageBox.critical(self, "Erreur", msg)

    def delete_compte(self, id_compte, num_compte):
        ans = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le compte N° {num_compte} ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            success, msg = CompteService.delete_compte(id_compte)
            if success:
                QMessageBox.information(self, "Succès", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur", msg)

    def clear_form(self):
        self.txt_num.clear()
        self.txt_lib.clear()
