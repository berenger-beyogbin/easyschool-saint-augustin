from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from services.famille_service import FamilleService
from views.famille_form_view import FamilleFormView
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SUCCESS, BUTTON_SECONDARY, BUTTON_DANGER,
    apply_table_style
)

class FamilleListView(QWidget):
    """
    Vue : LISTE DES FAMILLES
    Affiche l'ensemble des parents / responsables avec des raccourcis de modification.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # 1. En-tête de filtre / Titre
        header_layout = QHBoxLayout()
        titre = QLabel("Liste des Familles")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        header_layout.addWidget(titre)
        header_layout.addStretch()

        # Barre de recherche
        lbl_recherche = QLabel("Rechercher responsable :")
        lbl_recherche.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"
        )
        self.txt_recherche = QLineEdit()
        self.txt_recherche.setPlaceholderText("Saisir un nom ou numéro...")
        self.txt_recherche.setStyleSheet(INPUT_STYLE)
        self.txt_recherche.setFixedWidth(250)
        self.txt_recherche.textChanged.connect(self.load_data)
        
        header_layout.addWidget(lbl_recherche)
        header_layout.addWidget(self.txt_recherche)
        self.layout.addLayout(header_layout)

        # 2. Tableau d'affichage
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Responsable", "Profession", "Adresse", "Cellulaire",
            "Email", "Ebrie Abobote"
        ])
        
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_modifier)
        
        self.layout.addWidget(self.table)

        # 3. Barre de boutons d'action du bas
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SUCCESS)
        self.btn_nouveau.clicked.connect(self.on_nouveau)

        self.btn_modifier = QPushButton("Modifier")
        self.btn_modifier.setStyleSheet(BUTTON_PRIMARY)
        self.btn_modifier.clicked.connect(self.on_modifier)

        self.btn_supprimer = QPushButton("Supprimer")
        self.btn_supprimer.setStyleSheet(BUTTON_DANGER)
        self.btn_supprimer.clicked.connect(self.on_supprimer)

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.on_fermer)

        btn_layout.addWidget(self.btn_nouveau)
        btn_layout.addWidget(self.btn_modifier)
        btn_layout.addWidget(self.btn_supprimer)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_fermer)
        self.layout.addLayout(btn_layout)

    def load_data(self):
        """Récupère les familles et peuple le Grid."""
        self.table.setRowCount(0)
        query = self.txt_recherche.text().strip()
        familles = FamilleService.search_familles(query)

        for i, fam in enumerate(familles):
            self.table.insertRow(i)
            
            # Stocke l'ID confidentiellement sur la ligne
            self.table.setItem(i, 0, QTableWidgetItem(fam.NomResponsable))
            self.table.item(i, 0).setData(Qt.UserRole, fam.IdTFamille)
            
            self.table.setItem(i, 1, QTableWidgetItem(fam.ProfessionResponsable or ""))
            self.table.setItem(i, 2, QTableWidgetItem(fam.AdresseResponsable or ""))
            self.table.setItem(i, 3, QTableWidgetItem(fam.CellulaireResponsable or ""))
            self.table.setItem(i, 4, QTableWidgetItem(fam.EmailResponsable or ""))
            
            # Booléen sous forme d'indicateur textuel "OUI" ou "NON"
            self.table.setItem(i, 5, QTableWidgetItem("OUI" if fam.EbrieAbobote else "NON"))


    def get_selected_id(self) -> int | None:
        """Retourne l'ID de la famille sélectionnée."""
        selected_indexes = self.table.selectedIndexes()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        item = self.table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None

    def on_nouveau(self):
        dial = FamilleFormView(self)
        if dial.exec() == FamilleFormView.Accepted:
            self.load_data()

    def on_modifier(self):
        id_fam = self.get_selected_id()
        if not id_fam:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner une famille dans le tableau.")
            return
        
        dial = FamilleFormView(self, id_famille=id_fam)
        if dial.exec() == FamilleFormView.Accepted:
            self.load_data()

    def on_supprimer(self):
        id_fam = self.get_selected_id()
        if not id_fam:
            QMessageBox.warning(self, "Selection", "Veuillez selectionner une famille à supprimer.")
            return

        row = self.table.currentRow()
        nom_resp = self.table.item(row, 0).text()

        # Demander confirmation
        confirm = QMessageBox.question(
            self, "Confirmation", 
            f"Voulez-vous vraiment supprimer la famille du responsable '{nom_resp}' ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success, msg = FamilleService.delete_famille(id_fam)
            if success:
                QMessageBox.information(self, "Succes", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur de suppression", msg)

    def on_fermer(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()
        else:
            self.close()
