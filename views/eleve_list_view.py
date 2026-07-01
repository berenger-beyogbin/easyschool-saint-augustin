from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QDialog
)
from PySide6.QtCore import Qt
from services.eleve_service import EleveService
from views.eleve_form_view import EleveFormView
from app.styles import (
    COLORS, INPUT_STYLE, TABLE_STYLE, PAGE_TITLE_STYLE,
    BUTTON_PRIMARY, BUTTON_SUCCESS, BUTTON_SECONDARY, BUTTON_DANGER,
    apply_table_style
)

class EleveListView(QWidget):
    """
    Vue : INSCRIPTION ÉLÈVE (Liste des Élèves)
    Affiche la liste complète des élèves enregistrés, permettant modification et consultation des détails.
    """
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(12)

        # 1. En-tête : Titre et champ de recherche
        header = QHBoxLayout()
        titre = QLabel("Liste des Élèves")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        header.addWidget(titre)
        header.addStretch()

        lbl_rech = QLabel("Filtrer :")
        lbl_rech.setStyleSheet(
            f"font-size: 12px; color: {COLORS['muted']}; background-color: transparent;"
        )
        self.txt_recherche = QLineEdit()
        self.txt_recherche.setPlaceholderText("Nom, prénom ou matricule…")
        self.txt_recherche.setStyleSheet(INPUT_STYLE)
        self.txt_recherche.setFixedWidth(240)
        self.txt_recherche.textChanged.connect(self.load_data)

        header.addWidget(lbl_rech)
        header.addWidget(self.txt_recherche)
        self.layout.addLayout(header)

        # 2. Tableau de résultats
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Matricule", "Nom", "Prénoms", "Date Naiss", "Lieu Naiss",
            "Sexe", "Nationalité", "Religion", "Habitation"
        ])
        apply_table_style(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.on_modifier)
        self.layout.addWidget(self.table)

        # 3. Boutons d'action
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_nouveau = QPushButton("+ Nouveau")
        self.btn_nouveau.setStyleSheet(BUTTON_SUCCESS)
        self.btn_nouveau.clicked.connect(self.on_nouveau)

        self.btn_modifier = QPushButton("Modifier")
        self.btn_modifier.setStyleSheet(BUTTON_PRIMARY)
        self.btn_modifier.clicked.connect(self.on_modifier)

        self.btn_detail = QPushButton("Détail")
        self.btn_detail.setStyleSheet(BUTTON_PRIMARY)
        self.btn_detail.clicked.connect(self.on_detail)

        self.btn_supprimer = QPushButton("Supprimer")
        self.btn_supprimer.setStyleSheet(BUTTON_DANGER)
        self.btn_supprimer.clicked.connect(self.on_supprimer)

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        self.btn_fermer.clicked.connect(self.on_fermer)

        btn_layout.addWidget(self.btn_nouveau)
        btn_layout.addWidget(self.btn_modifier)
        btn_layout.addWidget(self.btn_detail)
        btn_layout.addWidget(self.btn_supprimer)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_fermer)
        self.layout.addLayout(btn_layout)

    def load_data(self):
        """Peuple le tableau des élèves."""
        self.table.setRowCount(0)
        query = self.txt_recherche.text().strip().lower()
        
        eleves = EleveService.get_all_eleves()
        
        row_idx = 0
        for i, el in enumerate(eleves):
            # Application du filtrage de recherche
            if query:
                nom_complet = f"{el.Nom} {el.Prenoms}".lower()
                if query not in el.Matricule.lower() and query not in nom_complet:
                    continue
            
            self.table.insertRow(row_idx)
            
            # Matricule avec ID de l’élève caché en UserRole
            item_mat = QTableWidgetItem(el.Matricule)
            item_mat.setData(Qt.UserRole, el.IDEleve)
            self.table.setItem(row_idx, 0, item_mat)
            
            self.table.setItem(row_idx, 1, QTableWidgetItem(el.Nom))
            self.table.setItem(row_idx, 2, QTableWidgetItem(el.Prenoms))
            
            # Formater date de naissance
            date_str = el.DateNaissance.strftime("%d/%m/%Y") if el.DateNaissance else ""
            self.table.setItem(row_idx, 3, QTableWidgetItem(date_str))
            
            self.table.setItem(row_idx, 4, QTableWidgetItem(el.LieuNaissance or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem("M" if el.Sexe == 1 else "F"))
            
            # Nationalité et religion
            nat_str = el.nationalite.Nationalite if el.nationalite else ""
            rel_str = el.religion.Religion if el.religion else ""
            self.table.setItem(row_idx, 6, QTableWidgetItem(nat_str))
            self.table.setItem(row_idx, 7, QTableWidgetItem(rel_str))
            
            self.table.setItem(row_idx, 8, QTableWidgetItem(el.Habitation or ""))
            
            row_idx += 1

    def get_selected_id(self) -> int | None:
        selected_indexes = self.table.selectedIndexes()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def on_nouveau(self):
        dial = EleveFormView(self)
        if dial.exec() == EleveFormView.Accepted:
            self.load_data()

    def on_modifier(self):
        id_el = self.get_selected_id()
        if not id_el:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un élève dans le tableau.")
            return
        
        dial = EleveFormView(self, id_eleve=id_el)
        if dial.exec() == EleveFormView.Accepted:
            self.load_data()

    def on_detail(self):
        id_el = self.get_selected_id()
        if not id_el:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un élève pour afficher les détails.")
            return

        el = EleveService.get_eleve_by_id(id_el)
        if not el:
            return

        # Construction d'un joli récapitulatif textuel complet
        sexe_lib = "Masculin" if el.Sexe == 1 else "Féminin"
        bday_str = el.DateNaissance.strftime("%d/%m/%Y") if el.DateNaissance else "Inconnue"
        
        nat_lib = el.nationalite.Nationalite if el.nationalite else "Non renseignée"
        rel_lib = el.religion.Religion if el.religion else "Non renseignée"
        
        responsable_details = "Aucun parent associé pour l'instant."
        if el.famille:
            rel_paren = "TUTEUR / RESPONSABLE"
            if el.famille.QualiteResponsable == 2:
                rel_paren = "PÈRE"
            elif el.famille.QualiteResponsable == 3:
                rel_paren = "MÈRE"
            responsable_details = (
                f"- Nom : {el.famille.NomResponsable}\n"
                f"- Qualité : {rel_paren}\n"
                f"- Téléphone : {el.famille.CellulaireResponsable}\n"
                f"- Email : {el.famille.EmailResponsable or 'Non renseigné'}\n"
                f"- Habitation : {el.famille.HabitationParent or 'Non renseignée'}"
            )

        details_msg = (
            f"=== FICHE SYNTHÉTIQUE DE L'ÉLÈVE ===\n\n"
            f"IDENTIFICATION :\n"
            f"- Matricule : {el.Matricule}\n"
            f"- Nom complet : {el.Nom} {el.Prenoms}\n"
            f"- Sexe : {sexe_lib}\n"
            f"- Né(e) le : {bday_str} à {el.LieuNaissance or 'Inconnu'}\n"
            f"- Nationalité : {nat_lib}\n"
            f"- Religion : {rel_lib}\n"
            f"- Habitation : {el.Habitation or 'Non spécifiée'}\n\n"
            
            f"ADMINISTRATIF EXTRAIT :\n"
            f"- N° Extrait : {el.NumExtrait or 'Non spécifié'}\n"
            f"- Délivré le : {el.DateExtrait.strftime('%d/%m/%Y') if el.DateExtrait else 'N/A'}\n"
            f"- Lieu délivrance : {el.LieuDelivrance or 'Non spécifié'}\n\n"
            
            f"RESPONSABLE LÉGAL :\n"
            f"{responsable_details}\n\n"
            
            f"CONTACT URGENCE :\n"
            f"- Nom : {el.NomUrgence or 'Non spécifié'}\n"
            f"- Contact : {el.ContactUrgence or 'Non spécifié'}\n"
            f"- Habitation : {el.HabitationUrgence or 'Non spécifiée'}\n"
        )

        # Affichage
        dial_details = QMessageBox(self)
        dial_details.setWindowTitle(f"Fiche détaillée - {el.Nom} {el.Prenoms}")
        dial_details.setText(details_msg)
        dial_details.setStandardButtons(QMessageBox.Ok)
        dial_details.exec()

    def on_supprimer(self):
        id_el = self.get_selected_id()
        if not id_el:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un élève à supprimer.")
            return

        row = self.table.currentRow()
        nom_eleve = f"{self.table.item(row, 1).text()} {self.table.item(row, 2).text()}"

        confirm = QMessageBox.question(
            self, "Confirmation de suppression",
            f"Voulez-vous vraiment supprimer définitivement l'élève '{nom_eleve}' de la base ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            success, msg = EleveService.delete_eleve(id_el)
            if success:
                QMessageBox.information(self, "Succès", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Erreur de suppression", msg)

    def on_fermer(self):
        if self.main_window and hasattr(self.main_window, "close_active_tab"):
            self.main_window.close_active_tab()
        else:
            self.close()
