from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from services.statistiques_service import StatistiquesService
from utils.list_printer import TransportStatPrinter
from app.styles import (
    COLORS, PAGE_TITLE_STYLE, SECTION_TITLE_STYLE,
    COMBO_STYLE, BUTTON_PRIMARY, BUTTON_SUCCESS,
    apply_table_style, make_totaux_panel_widget
)


class StatTransportView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.load_filters()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        titre = QLabel("État des Versements de Transport")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(titre)

        lbl_section = QLabel("Suivi des versements de transport par élève")
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
            "N°", "Matricule", "Nom et Prénoms", "Classe", "Montant dû", "Montant versé", "Reste", "État"
        ])
        apply_table_style(self.table, alternate="yellow")

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

        self.totaux_panel, (
            self.lbl_tot_du,
            self.lbl_tot_verse,
            self.lbl_tot_reste,
        ) = make_totaux_panel_widget([
            ("Total dû",     COLORS['primary']),
            ("Total versé",  COLORS['success']),
            ("Reste global", COLORS['warning']),
        ])
        layout.addWidget(self.totaux_panel)

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

        data = StatistiquesService.get_etat_versements_transport(id_niveau, id_classe)

        self.table.setRowCount(0)
        self.table.setRowCount(len(data))

        sum_du = 0.0
        sum_verse = 0.0
        sum_reste = 0.0

        for idx, item in enumerate(data):
            sum_du += item["MontantDu"]
            sum_verse += item["MontantVerse"]
            sum_reste += item["Reste"]

            it_idx = QTableWidgetItem(str(idx + 1))
            it_idx.setTextAlignment(Qt.AlignCenter)

            it_matr = QTableWidgetItem(item["Matricule"] or "")
            it_matr.setTextAlignment(Qt.AlignCenter)

            it_nom = QTableWidgetItem(item["Nom"].upper())
            it_classe = QTableWidgetItem(item["LibClasse"] or "")

            it_du = QTableWidgetItem(StatistiquesService.format_fcfa(item["MontantDu"]))
            it_du.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_verse = QTableWidgetItem(StatistiquesService.format_fcfa(item["MontantVerse"]))
            it_verse.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_reste = QTableWidgetItem(StatistiquesService.format_fcfa(item["Reste"]))
            it_reste.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            it_etat = QTableWidgetItem(item["Etat"])
            it_etat.setTextAlignment(Qt.AlignCenter)
            if item["Etat"] == "Payé":
                it_etat.setForeground(QColor(COLORS["success"]))
            elif item["Etat"] == "Partiel":
                it_etat.setForeground(QColor(COLORS["warning"]))
            else:
                it_etat.setForeground(QColor(COLORS["danger"]))

            self.table.setItem(idx, 0, it_idx)
            self.table.setItem(idx, 1, it_matr)
            self.table.setItem(idx, 2, it_nom)
            self.table.setItem(idx, 3, it_classe)
            self.table.setItem(idx, 4, it_du)
            self.table.setItem(idx, 5, it_verse)
            self.table.setItem(idx, 6, it_reste)
            self.table.setItem(idx, 7, it_etat)

        self.lbl_tot_du.setText(StatistiquesService.format_fcfa(sum_du))
        self.lbl_tot_verse.setText(StatistiquesService.format_fcfa(sum_verse))
        self.lbl_tot_reste.setText(StatistiquesService.format_fcfa(sum_reste))

    def imprimer_clic(self):
        id_niveau = self.cmb_niveau.currentData()
        id_classe = self.cmb_classe.currentData()
        data = StatistiquesService.get_etat_versements_transport(id_niveau, id_classe)
        if not data:
            QMessageBox.information(self, "Impression", "Aucune donnée à imprimer.")
            return

        filtre = ""
        if self.cmb_classe.currentData():
            filtre = self.cmb_classe.currentText()
        elif self.cmb_niveau.currentData():
            filtre = self.cmb_niveau.currentText()

        TransportStatPrinter.print_report(self, data, filtre)
