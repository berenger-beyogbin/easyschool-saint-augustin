from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.session import AppSession
from app.styles import BUTTON_PRIMARY, COLORS, COMBO_STYLE, TABLE_STYLE
from services.echeancier_service import EcheancierService


class EcheancierView(QWidget):
    """Parametrage des tranches de scolarite, transport et cantine."""

    PROFILS = [
        ("Scolarité — Préscolaire", EcheancierService.SCOLARITE, EcheancierService.PRESCOLAIRE),
        ("Scolarité — Nouveau CP1 à CM2", EcheancierService.SCOLARITE, EcheancierService.NOUVEAU_PRIMAIRE),
        ("Scolarité — Ancien CP1 à CM2", EcheancierService.SCOLARITE, EcheancierService.ANCIEN_PRIMAIRE),
        ("Transport — Tous les niveaux", EcheancierService.TRANSPORT, EcheancierService.TOUS),
        ("Cantine — Tous les niveaux", EcheancierService.CANTINE, EcheancierService.TOUS),
    ]

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        titre = QLabel("Échéanciers de paiement")
        titre.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {COLORS['text']};"
        )
        layout.addWidget(titre)

        aide = QLabel(
            "Configurez les tranches attendues. La première est exigible à la date "
            "d'inscription ; les suivantes utilisent leur date limite."
        )
        aide.setWordWrap(True)
        aide.setStyleSheet(f"color: {COLORS['muted']}; font-size: 12px;")
        layout.addWidget(aide)

        ligne = QHBoxLayout()
        ligne.addWidget(QLabel("Barème :"))
        self.cmb_profil = QComboBox()
        self.cmb_profil.setStyleSheet(COMBO_STYLE)
        for libelle, type_frais, categorie in self.PROFILS:
            self.cmb_profil.addItem(libelle, (type_frais, categorie))
        self.cmb_profil.currentIndexChanged.connect(self.load_data)
        ligne.addWidget(self.cmb_profil, 1)

        self.lbl_total = QLabel("Total : 0 F")
        self.lbl_total.setStyleSheet(
            f"font-weight: 800; color: {COLORS['primary']}; font-size: 14px;"
        )
        ligne.addWidget(self.lbl_total)
        layout.addLayout(ligne)

        self.table = QTableWidget(3, 4)
        self.table.setHorizontalHeaderLabels(["Tranche", "Libellé", "Date limite", "Montant (F CFA)"])
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self._actualiser_total)
        layout.addWidget(self.table)

        pied = QHBoxLayout()
        pied.addStretch()
        self.btn_enregistrer = QPushButton("Enregistrer l'échéancier")
        self.btn_enregistrer.setStyleSheet(BUTTON_PRIMARY)
        self.btn_enregistrer.clicked.connect(self.save_data)
        pied.addWidget(self.btn_enregistrer)
        layout.addLayout(pied)

        self.load_data()

    def load_data(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            self.table.setRowCount(0)
            return
        type_frais, categorie = self.cmb_profil.currentData()
        tranches = EcheancierService.get_tranches(id_annee, type_frais, categorie)
        self.table.blockSignals(True)
        self.table.setRowCount(len(tranches))
        for row, tranche in enumerate(tranches):
            numero = QTableWidgetItem(str(tranche["numero"]))
            numero.setFlags(numero.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, numero)
            self.table.setItem(row, 1, QTableWidgetItem(tranche["libelle"]))
            date_txt = (
                tranche["date_echeance"].strftime("%d/%m/%Y")
                if tranche["date_echeance"] else "À l'inscription"
            )
            date_item = QTableWidgetItem(date_txt)
            if tranche["date_echeance"] is None:
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, date_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(int(tranche["montant"]))))
        self.table.blockSignals(False)
        self._actualiser_total()

    def _actualiser_total(self):
        total = 0
        for row in range(self.table.rowCount()):
            try:
                total += int(self.table.item(row, 3).text().replace(" ", ""))
            except (AttributeError, ValueError):
                pass
        self.lbl_total.setText(f"Total : {total:,} F".replace(",", " "))

    def save_data(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            QMessageBox.warning(self, "Année", "Aucune année scolaire active.")
            return
        type_frais, categorie = self.cmb_profil.currentData()
        tranches = []
        try:
            for row in range(self.table.rowCount()):
                date_txt = self.table.item(row, 2).text().strip()
                date_echeance = None
                if row > 0:
                    date_echeance = datetime.strptime(date_txt, "%d/%m/%Y").date()
                tranches.append({
                    "numero": row + 1,
                    "libelle": self.table.item(row, 1).text().strip(),
                    "date_echeance": date_echeance,
                    "montant": float(self.table.item(row, 3).text().replace(" ", "")),
                })
        except (AttributeError, TypeError, ValueError):
            QMessageBox.warning(
                self, "Saisie incorrecte",
                "Vérifiez les montants et les dates au format JJ/MM/AAAA.",
            )
            return

        success, message = EcheancierService.remplacer_tranches(
            id_annee, type_frais, categorie, tranches
        )
        if success:
            QMessageBox.information(self, "Échéancier", message)
            self.load_data()
        else:
            QMessageBox.critical(self, "Échéancier", message)

