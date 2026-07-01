from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from services.statistiques_service import StatistiquesService
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    COMBO_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    apply_table_style
)
from utils.list_printer import ListeAlphabetiquePrinter


class ListeAlphabetiqueView(QWidget):
    """Liste alphabétique des élèves par classe, avec contact du responsable légal — impression officielle."""

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.init_ui()
        self.load_filters()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        titre = QLabel("Liste Alphabétique")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        lbl_section = QLabel("Liste alphabétique des élèves par classe")
        lbl_section.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(lbl_section)

        lbl_style = f"font-size: 12px; color: {COLORS['text_soft']}; background-color: transparent;"

        layout_filtres = QHBoxLayout()
        layout_filtres.setSpacing(10)

        lbl_niveau = QLabel("Niveau :")
        lbl_niveau.setStyleSheet(lbl_style)
        self.cmb_niveau = QComboBox()
        self.cmb_niveau.setStyleSheet(COMBO_STYLE)
        self.cmb_niveau.setMinimumWidth(150)
        self.cmb_niveau.currentIndexChanged.connect(self.on_niveau_changed)

        lbl_classe = QLabel("Classe :")
        lbl_classe.setStyleSheet(lbl_style)
        self.cmb_classe = QComboBox()
        self.cmb_classe.setStyleSheet(COMBO_STYLE)
        self.cmb_classe.setMinimumWidth(150)

        self.btn_afficher = QPushButton("Afficher")
        self.btn_afficher.setStyleSheet(BUTTON_PRIMARY)
        self.btn_afficher.clicked.connect(self.refresh_data)

        self.btn_imprimer = QPushButton("Imprimer")
        self.btn_imprimer.setStyleSheet(BUTTON_SUCCESS)
        self.btn_imprimer.clicked.connect(self.imprimer_clic)

        layout_filtres.addWidget(lbl_niveau)
        layout_filtres.addWidget(self.cmb_niveau)
        layout_filtres.addWidget(lbl_classe)
        layout_filtres.addWidget(self.cmb_classe)
        layout_filtres.addWidget(self.btn_afficher)
        layout_filtres.addWidget(self.btn_imprimer)
        layout_filtres.addStretch()

        layout.addLayout(layout_filtres)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "N°", "Matricule", "Nom et Prénoms", "Classe",
            "Date de Naissance", "Sexe", "Profession", "Téléphone"
        ])
        apply_table_style(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

    def load_filters(self):
        self.cmb_niveau.blockSignals(True)
        self.cmb_niveau.clear()
        self.cmb_niveau.addItem("-- Tous les niveaux --", None)
        niveaux = StatistiquesService.get_niveaux()
        for niv in niveaux:
            self.cmb_niveau.addItem(niv["Libelle"], niv["IDT_Niveau"])
        self.cmb_niveau.blockSignals(False)

        self.load_classes_filter(None)

    def load_classes_filter(self, id_niveau):
        self.cmb_classe.clear()
        self.cmb_classe.addItem("-- Toutes les classes --", None)
        classes = StatistiquesService.get_classes_by_niveau(id_niveau)
        for cls in classes:
            self.cmb_classe.addItem(cls["LibClasse"], cls["IDTClasse"])

    def on_niveau_changed(self):
        id_niveau = self.cmb_niveau.currentData()
        self.load_classes_filter(id_niveau)

    def refresh_data(self):
        id_niveau = self.cmb_niveau.currentData()
        id_classe = self.cmb_classe.currentData()

        data = StatistiquesService.get_liste_alphabetique(id_niveau, id_classe)

        self.table.setRowCount(0)
        self.table.setRowCount(len(data))

        for idx, item in enumerate(data):
            matr      = item["Matricule"] or ""
            noms      = f"{item['Nom']} {item['Prenoms']}".upper()
            classe    = item["LibClasse"] or ""
            d_naiss   = item["DateNaissance"].strftime("%d/%m/%Y") if item["DateNaissance"] else ""
            sexe      = "M" if item.get("Sexe") == 1 else "F"
            profession = item.get("Profession") or ""
            telephone  = item.get("Telephone") or ""

            it_idx = QTableWidgetItem(str(idx + 1))
            it_idx.setTextAlignment(Qt.AlignCenter)

            it_matr = QTableWidgetItem(matr)
            it_matr.setTextAlignment(Qt.AlignCenter)

            it_noms = QTableWidgetItem(noms)
            it_classe = QTableWidgetItem(classe)

            it_naiss = QTableWidgetItem(d_naiss)
            it_naiss.setTextAlignment(Qt.AlignCenter)

            it_sexe = QTableWidgetItem(sexe)
            it_sexe.setTextAlignment(Qt.AlignCenter)

            it_prof = QTableWidgetItem(profession)
            it_tel  = QTableWidgetItem(telephone)

            self.table.setItem(idx, 0, it_idx)
            self.table.setItem(idx, 1, it_matr)
            self.table.setItem(idx, 2, it_noms)
            self.table.setItem(idx, 3, it_classe)
            self.table.setItem(idx, 4, it_naiss)
            self.table.setItem(idx, 5, it_sexe)
            self.table.setItem(idx, 6, it_prof)
            self.table.setItem(idx, 7, it_tel)

    def imprimer_clic(self):
        id_niveau = self.cmb_niveau.currentData()
        id_classe = self.cmb_classe.currentData()
        data = StatistiquesService.get_liste_alphabetique(id_niveau, id_classe)
        if not data:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return

        filtre = ""
        if self.cmb_classe.currentData():
            filtre = self.cmb_classe.currentText()
        elif self.cmb_niveau.currentData():
            filtre = self.cmb_niveau.currentText()

        ListeAlphabetiquePrinter.print_report(self, data, filtre)
