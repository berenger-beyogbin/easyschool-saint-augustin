from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from services.annee_scolaire_service import AnneeScolaireService
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, INPUT_STYLE,
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_SUCCESS, BUTTON_WARNING,
    BUTTON_TABLE_ACTION_WARNING,
    apply_table_style, configure_table_action_button, make_table_action_container
)

class AnneeScolaireView(QWidget):
    """
    Ecran : CREATION ANNEE SCOLAIRE
    Permet de lister, creer et cloturer les annees scolaires.
    """
    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Titre
        titre = QLabel("Création & Gestion des Années Scolaires")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        self.layout.addWidget(titre)

        # Formulaire de Creation
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        lbl = QLabel("Nouvelle Année Scolaire (Format YYYY-YYYY) * :")
        lbl.setStyleSheet(f"font-weight: 600; color: {COLORS['text_soft']}; background-color: transparent;")
        self.txt_annee = QLineEdit()
        self.txt_annee.setPlaceholderText("Ex: 2026-2027")
        self.txt_annee.setStyleSheet(INPUT_STYLE)
        self.txt_annee.setMaximumWidth(250)

        self.btn_nouveau = QPushButton("Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SECONDARY)
        self.btn_nouveau.clicked.connect(self.clear_fields)

        self.btn_valider = QPushButton("✓  Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.save_annee)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        form_layout.addWidget(lbl)
        form_layout.addWidget(self.txt_annee)
        form_layout.addWidget(self.btn_nouveau)
        form_layout.addWidget(self.btn_valider)
        form_layout.addWidget(btn_fermer)
        form_layout.addStretch()
        self.layout.addLayout(form_layout)

        # Tableau des annees
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Année Scolaire", "Statut", "Action Clôturer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        apply_table_style(self.table)
        self.layout.addWidget(self.table)

    def load_data(self):
        """Met a jour la liste des annees scolaires dans le tableau."""
        self.table.setRowCount(0)
        annees = AnneeScolaireService.get_all()
        for i, annee in enumerate(annees):
            self.table.insertRow(i)
            
            # Libelle de l'annee
            self.table.setItem(i, 0, QTableWidgetItem(annee.Libelle))
            
            # Statut
            statut_txt = "Clôturée" if annee.Cloturer else "Active"
            item_statut = QTableWidgetItem(statut_txt)
            if annee.Cloturer:
                item_statut.setForeground(QColor(COLORS["danger"]))
            else:
                item_statut.setForeground(QColor(COLORS["success"]))
            self.table.setItem(i, 1, item_statut)

            # Bouton Cloturer
            if not annee.Cloturer:
                btn_cloture = QPushButton("Clôturer")
                configure_table_action_button(btn_cloture, "warning")
                btn_cloture.clicked.connect(lambda checked=False, id_a=annee.IDTAnneeScolaire, lib=annee.Libelle: self.cloturer_annee(id_a, lib))
                self.table.setCellWidget(i, 2, make_table_action_container(btn_cloture))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("Déjà clôturée"))
            self.table.setRowHeight(i, 44)

    def save_annee(self):
        lib = self.txt_annee.text().strip()
        if not lib:
            QMessageBox.warning(self, "Champ obligatoire", "Veuillez saisir l'année scolaire !")
            return

        reussite, msg = AnneeScolaireService.add_annee(lib)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", msg)
            self.txt_annee.clear()
            self.load_data()
            self.data_changed.emit()
        else:
            QMessageBox.warning(self, "Attention", msg)

    def cloturer_annee(self, id_annee, libelle):
        reponse = QMessageBox.question(
            self, "Confirmer la clôture", 
            f"Voulez-vous vraiment clôturer l'année {libelle} ? \nCette action est irréversible !",
            QMessageBox.Yes | QMessageBox.No
        )
        if reponse == QMessageBox.Yes:
            if AnneeScolaireService.cloturer_annee(id_annee):
                QMessageBox.information(self, "Modification réussie", f"L'année scolaire {libelle} est désormais close.")
                self.load_data()
                self.data_changed.emit()
            else:
                QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de la clôture.")

    def clear_fields(self):
        """Réinitialise les champs de saisie."""
        self.txt_annee.clear()
        self.txt_annee.setFocus()

    def refresh_data(self):
        """Rafraîchit la liste des données."""
        self.load_data()

    def close_tab(self):
        self.clear_fields()
