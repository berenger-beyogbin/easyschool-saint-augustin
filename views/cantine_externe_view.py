from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QInputDialog, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from app.session import AppSession
from app.styles import (
    BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_TABLE_ACTION_PRIMARY,
    COLORS, COMBO_STYLE, INPUT_STYLE, MESSAGEBOX_STYLE, TABLE_STYLE, TAB_STYLE,
)
from services.cantine_externe_service import CantineExterneService
from utils.receipt_printer import ReceiptPrinter
from views.ui_components import KpiCard


def _money(value) -> str:
    return f"{int(value):,} FCFA".replace(",", " ")


def _section_title(title: str, help_text: str) -> QFrame:
    frame = QFrame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 4, 0, 8)
    layout.setSpacing(2)
    label = QLabel(title)
    label.setStyleSheet(f"font-size:18px; font-weight:700; color:{COLORS['text']};")
    help_label = QLabel(help_text)
    help_label.setWordWrap(True)
    help_label.setStyleSheet(f"color:{COLORS['muted']};")
    layout.addWidget(label)
    layout.addWidget(help_label)
    return frame


class PensionnaireCantineDialog(QDialog):
    """Saisie minimale d'un pensionnaire cantine, sans dossier scolaire."""

    def __init__(self, montant_tarif, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau pensionnaire cantine")
        self.setMinimumWidth(560)
        form = QFormLayout(self)
        form.addRow("Tarif annuel :", QLabel(_money(montant_tarif)))
        self.nom = QLineEdit()
        self.prenoms = QLineEdit()
        self.date_naissance = QDateEdit(QDate.currentDate().addYears(-10))
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setMaximumDate(QDate.currentDate())
        self.sexe = QComboBox()
        self.sexe.addItem("Masculin", 1)
        self.sexe.addItem("Féminin", 2)
        self.lieu_naissance = QLineEdit()
        self.habitation = QLineEdit()
        self.responsable_nom = QLineEdit()
        self.responsable_contact = QLineEdit()
        for field in (
            self.nom, self.prenoms, self.lieu_naissance, self.habitation,
            self.responsable_nom, self.responsable_contact,
        ):
            field.setStyleSheet(INPUT_STYLE)
        self.sexe.setStyleSheet(COMBO_STYLE)
        self.responsable_contact.setPlaceholderText("Téléphone")
        form.addRow("Nom * :", self.nom)
        form.addRow("Prénoms * :", self.prenoms)
        form.addRow("Date de naissance * :", self.date_naissance)
        form.addRow("Sexe * :", self.sexe)
        form.addRow("Lieu de naissance :", self.lieu_naissance)
        form.addRow("Habitation :", self.habitation)
        form.addRow("Responsable * :", self.responsable_nom)
        form.addRow("Contact du responsable * :", self.responsable_contact)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Créer et inscrire")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validate(self):
        required = (self.nom, self.prenoms, self.responsable_nom, self.responsable_contact)
        if any(not field.text().strip() for field in required):
            QMessageBox.warning(self, "Pensionnaire cantine", "Renseignez tous les champs marqués d’un astérisque.")
            return
        self.accept()

    def values(self):
        qdate = self.date_naissance.date()
        return {
            "nom": self.nom.text(), "prenoms": self.prenoms.text(),
            "date_naissance": date(qdate.year(), qdate.month(), qdate.day()),
            "sexe": self.sexe.currentData(),
            "lieu_naissance": self.lieu_naissance.text(),
            "habitation": self.habitation.text(),
            "responsable_nom": self.responsable_nom.text(),
            "responsable_contact": self.responsable_contact.text(),
        }


class VersementCantineDialog(QDialog):
    def __init__(self, pensionnaire: dict, parent=None):
        super().__init__(parent)
        self.pensionnaire = pensionnaire
        self.receipt_data = None
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumWidth(470)
        form = QFormLayout(self)
        name = QLabel(pensionnaire["nom"])
        name.setStyleSheet("font-weight:700;")
        rest = QLabel(_money(pensionnaire["reste"]))
        rest.setStyleSheet(f"font-weight:700; color:{COLORS['danger']};")
        form.addRow("Pensionnaire :", name)
        form.addRow("Reste à payer :", rest)
        self.montant = QLineEdit()
        self.montant.setPlaceholderText("Ex. 10 000")
        self.montant.setStyleSheet(INPUT_STYLE)
        self.mode = QComboBox()
        self.mode.setStyleSheet(COMBO_STYLE)
        self.mode.addItems(["ESPÈCES", "CHÈQUE"])
        self.reference = QLineEdit()
        self.reference.setPlaceholderText("Facultative")
        self.reference.setStyleSheet(INPUT_STYLE)
        form.addRow("Montant * :", self.montant)
        form.addRow("Mode de paiement :", self.mode)
        form.addRow("Référence :", self.reference)
        self.date_versement = QDateEdit(QDate.currentDate())
        self.date_versement.setCalendarPopup(True)
        self.date_versement.setDisplayFormat("dd/MM/yyyy")
        self.date_versement.setMaximumDate(QDate.currentDate())
        form.addRow("Date du versement :", self.date_versement)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer le paiement")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _save(self):
        try:
            montant = float(self.montant.text().replace(" ", "").replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Paiement", "Saisissez un montant numérique valide.")
            return
        qd = self.date_versement.date()
        date_versement = date(qd.year(), qd.month(), qd.day())
        ok, message = CantineExterneService.verser(
            self.pensionnaire["id"], montant, self.mode.currentText(), self.reference.text(),
            date_versement,
        )
        if ok:
            numero_recu = message.partition("Reçu ")[2].rstrip(".") or "—"
            self.receipt_data = {
                "preview_title": "Aperçu — Reçu de paiement cantine",
                "receipt_title": "REÇU DE PAIEMENT — CANTINE EXTERNE",
                "scol_label": "CANTINE",
                "date": date_versement.strftime("%d/%m/%Y"),
                "matricule": self.pensionnaire.get("matricule", ""),
                "nom": self.pensionnaire.get("nom", ""),
                "classe": "",
                "numero": numero_recu,
                "motif": "Cantine externe",
                "mode_paiement": self.mode.currentText(),
                "total_recu": montant,
                "scol_active": True,
                "scol_due": self.pensionnaire.get("reste", 0),
                "scol_recu": montant,
                "scol_reste": max(0, self.pensionnaire.get("reste", 0) - montant),
                "autres_active": False,
                "trans_active": False,
                "cant_active": False,
            }
            QMessageBox.information(self, "Paiement enregistré", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Paiement", message)


class CantineExterneView(QWidget):
    TAB_DASHBOARD = 0
    TAB_PENSIONNAIRES = 1
    TAB_PAIEMENTS = 2
    TAB_TARIF = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._payment_rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        title = QLabel("CANTINE")
        title.setStyleSheet(f"font-size:22px; font-weight:800; color:{COLORS['primary_dark']};")
        subtitle = QLabel("Inscrire un pensionnaire hors base élèves, encaisser et suivre son solde")
        subtitle.setStyleSheet(f"color:{COLORS['muted']}; margin-bottom:8px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._build_dashboard(), "Vue d’ensemble")
        self.tabs.addTab(self._build_pensionnaires(), "Pensionnaires")
        self.tabs.addTab(self._build_payments(), "Paiements")
        self.tabs.addTab(self._build_tarif(), "Tarif")
        self.tabs.currentChanged.connect(lambda _: self.refresh_data())
        root.addWidget(self.tabs)

    def _build_dashboard(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        actions = QHBoxLayout()
        actions.addWidget(_section_title(
            "Que souhaitez-vous faire ?",
            "Inscrivez un pensionnaire ou enregistrez directement un paiement.",
        ), 1)
        btn_register = QPushButton("+ Inscrire un pensionnaire")
        btn_register.setStyleSheet(BUTTON_PRIMARY)
        btn_register.clicked.connect(self._go_to_registration)
        btn_pay = QPushButton("Enregistrer un paiement")
        btn_pay.setStyleSheet(BUTTON_SECONDARY)
        btn_pay.clicked.connect(self._go_to_payment)
        actions.addWidget(btn_register)
        actions.addWidget(btn_pay)
        layout.addLayout(actions)

        row1, row2 = QHBoxLayout(), QHBoxLayout()
        self.cards = {}
        specs = [
            ("effectif", "Pensionnaires", COLORS["primary"]),
            ("soldes", "Soldés", COLORS["success"]),
            ("en_cours", "En cours", COLORS["warning"]),
            ("attendu", "Cantine attendue", COLORS["purple"]),
            ("encaisse", "Cantine encaissée", COLORS["success"]),
            ("reste", "Reste à recouvrer", COLORS["danger"]),
        ]
        for index, (key, label, color) in enumerate(specs):
            card = KpiCard(label, color)
            self.cards[key] = card
            (row1 if index < 3 else row2).addWidget(card)
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addStretch()
        return widget

    def _build_pensionnaires(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(_section_title(
            "Inscrire et suivre les pensionnaires",
            "Le pensionnaire cantine n'a pas besoin d'être inscrit à l'école.",
        ), 1)
        btn_new = QPushButton("+ Inscrire un pensionnaire")
        btn_new.setStyleSheet(BUTTON_PRIMARY)
        btn_new.clicked.connect(self._inscrire)
        header.addWidget(btn_new)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.search_pensionnaire = QLineEdit()
        self.search_pensionnaire.setPlaceholderText("Rechercher par nom ou matricule…")
        self.search_pensionnaire.setStyleSheet(INPUT_STYLE)
        self.search_pensionnaire.setFixedHeight(38)
        self.search_pensionnaire.textChanged.connect(self._filter_pensionnaires)
        self.filter_status = QComboBox()
        self.filter_status.setStyleSheet(COMBO_STYLE)
        self.filter_status.addItem("Tous les statuts", "")
        self.filter_status.addItem("En cours", "EN_COURS")
        self.filter_status.addItem("Soldés", "SOLDE")
        self.filter_status.setFixedHeight(38)
        self.filter_status.currentIndexChanged.connect(self._filter_pensionnaires)
        filters.addWidget(self.search_pensionnaire, 1)
        filters.addWidget(self.filter_status)
        layout.addLayout(filters)

        self.table_pensionnaires = QTableWidget(0, 7)
        self.table_pensionnaires.setHorizontalHeaderLabels([
            "Matricule", "Nom et prénoms", "Responsable", "Total", "Versé", "Reste", "Actions",
        ])
        self.table_pensionnaires.setStyleSheet(TABLE_STYLE)
        self.table_pensionnaires.setAlternatingRowColors(True)
        self.table_pensionnaires.verticalHeader().setDefaultSectionSize(44)
        self.table_pensionnaires.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # Les widgets de cellule ne comptent pas dans ResizeToContents : largeur fixe.
        self.table_pensionnaires.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table_pensionnaires.setColumnWidth(6, 210)
        layout.addWidget(self.table_pensionnaires)
        return widget

    def _build_payments(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(_section_title(
            "Historique des paiements",
            "Consultez les reçus et les annulations de la cantine externe.",
        ), 1)
        new_payment = QPushButton("+ Nouveau paiement")
        new_payment.setStyleSheet(BUTTON_PRIMARY)
        new_payment.clicked.connect(self._choose_pensionnaire_to_pay)
        header.addWidget(new_payment)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.search_payment = QLineEdit()
        self.search_payment.setPlaceholderText("Rechercher un reçu ou un pensionnaire…")
        self.search_payment.setStyleSheet(INPUT_STYLE)
        self.search_payment.setFixedHeight(38)
        self.search_payment.textChanged.connect(self._filter_payments)
        self.filter_payment = QComboBox()
        self.filter_payment.setStyleSheet(COMBO_STYLE)
        self.filter_payment.addItem("Tous les paiements", "ALL")
        self.filter_payment.addItem("Validés", "VALID")
        self.filter_payment.addItem("Annulés", "CANCELLED")
        self.filter_payment.setFixedHeight(38)
        self.filter_payment.currentIndexChanged.connect(self._filter_payments)
        filters.addWidget(self.search_payment, 1)
        filters.addWidget(self.filter_payment)
        layout.addLayout(filters)

        self.table_versements = QTableWidget(0, 5)
        self.table_versements.setHorizontalHeaderLabels([
            "N° de reçu", "Date", "Pensionnaire", "Montant", "Mode",
        ])
        self.table_versements.setStyleSheet(TABLE_STYLE)
        self.table_versements.setAlternatingRowColors(True)
        self.table_versements.verticalHeader().setDefaultSectionSize(48)
        self.table_versements.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_versements.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_versements.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_versements.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table_versements)
        return widget

    def _build_tarif(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.addWidget(_section_title(
            "Tarif de la cantine externe",
            "Ce montant s'applique uniquement aux prochaines inscriptions (les inscriptions déjà créées gardent leur montant figé).",
        ))
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;}")
        form = QHBoxLayout(form_frame)
        form.setContentsMargins(16, 14, 16, 14)
        self.spin_tarif = QSpinBox()
        self.spin_tarif.setRange(0, 10_000_000)
        self.spin_tarif.setSingleStep(5_000)
        self.spin_tarif.setSuffix(" FCFA")
        self.spin_tarif.setStyleSheet(INPUT_STYLE)
        self.spin_tarif.setMinimumWidth(200)
        btn_save = QPushButton("Enregistrer")
        btn_save.setStyleSheet(BUTTON_PRIMARY)
        btn_save.clicked.connect(self._save_tarif)
        form.addWidget(QLabel("Montant annuel :"))
        form.addWidget(self.spin_tarif)
        form.addWidget(btn_save)
        form.addStretch()
        layout.addWidget(form_frame)
        layout.addStretch()
        return widget

    def refresh_data(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return
        stats = CantineExterneService.dashboard(id_annee)
        for key, card in self.cards.items():
            value = stats[key]
            card.set_value(_money(value) if key in {"attendu", "encaisse", "reste"} else str(value))
        self._rows = CantineExterneService.get_pensionnaires(id_annee)
        self._filter_pensionnaires()
        self._payment_rows = CantineExterneService.get_versements(id_annee)
        self._filter_payments()
        self.spin_tarif.setValue(int(CantineExterneService.get_tarif(id_annee)))

    load_data = refresh_data

    def _filter_pensionnaires(self, *_):
        query = self.search_pensionnaire.text().strip().casefold()
        status = self.filter_status.currentData()
        rows = [
            row for row in self._rows
            if (not query or query in f"{row['matricule']} {row['nom']}".casefold())
            and (not status or row["statut"] == status)
        ]
        self._load_pensionnaires(rows)

    def _load_pensionnaires(self, rows):
        table = self.table_pensionnaires
        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["matricule"], row["nom"], row["responsable"],
                _money(row["montant"]), _money(row["verse"]), _money(row["reste"]),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col in (3, 4, 5):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, col, item)
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(3, 3, 3, 3)
            actions_layout.setSpacing(4)
            payer = QPushButton("Paiement")
            payer.setToolTip("Enregistrer un paiement")
            payer.setFixedSize(88, 32)
            payer.setEnabled(row["reste"] > 0)
            payer.setStyleSheet(BUTTON_TABLE_ACTION_PRIMARY)
            payer.clicked.connect(lambda checked=False, r=row: self._payer(r))
            actions_layout.addWidget(payer)
            if AppSession.has_permission("CANTINE_EXTERNE_ADMISSIONS"):
                suppr = QPushButton("Supprimer")
                suppr.setToolTip("Supprimer ce pensionnaire (erreur de saisie)")
                suppr.setFixedSize(88, 32)
                if row["verse"] > 0:
                    suppr.setEnabled(False)
                    suppr.setToolTip("Suppression impossible : des versements existent")
                suppr.setStyleSheet(
                    "QPushButton { color: #DC2626; background: transparent; border: 1px solid #DC2626; "
                    "border-radius: 6px; font-weight: 700; } QPushButton:hover { background-color: #FEF2F2; } "
                    "QPushButton:disabled { color: #9CA3AF; border-color: #D1D5DB; }"
                )
                suppr.clicked.connect(lambda checked=False, r=row: self._supprimer(r))
                actions_layout.addWidget(suppr)
            table.setCellWidget(i, 6, actions)

    def _filter_payments(self, *_):
        query = self.search_payment.text().strip().casefold()
        state = self.filter_payment.currentData()
        rows = [
            row for row in self._payment_rows
            if (not query or query in f"{row['recu']} {row['nom']}".casefold())
            and (state == "ALL" or (state == "CANCELLED") == bool(row["annule"]))
        ]
        self._load_payments(rows)

    def _load_payments(self, rows):
        self.table_versements.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["recu"], row["date"].strftime("%d/%m/%Y"), row["nom"],
                _money(row["montant"]), row["mode"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_versements.setItem(i, col, item)

    def _go_to_registration(self):
        self.tabs.setCurrentIndex(self.TAB_PENSIONNAIRES)
        self._inscrire()

    def _go_to_payment(self):
        self.tabs.setCurrentIndex(self.TAB_PAIEMENTS)
        self._choose_pensionnaire_to_pay()

    def _choose_pensionnaire_to_pay(self):
        candidates = [row for row in self._rows if row["reste"] > 0]
        if not candidates:
            QMessageBox.information(self, "Paiement", "Aucun pensionnaire n’a de solde à payer.")
            return
        labels = [f"{row['matricule']} — {row['nom']} — reste {_money(row['reste'])}" for row in candidates]
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Nouveau paiement")
        dialog.setLabelText("Sélectionnez le pensionnaire :")
        dialog.setComboBoxItems(labels)
        dialog.setComboBoxEditable(False)
        dialog.setStyleSheet(MESSAGEBOX_STYLE)
        buttons = dialog.findChild(QDialogButtonBox)
        if buttons is not None:
            ok_button = buttons.button(QDialogButtonBox.Ok)
            if ok_button is not None:
                ok_button.setText("Valider")
        combo = dialog.findChild(QComboBox)
        if combo is not None:
            combo.setStyleSheet(COMBO_STYLE)
        if dialog.exec() == QDialog.Accepted:
            selected = dialog.textValue()
            self._payer(candidates[labels.index(selected)])

    def _inscrire(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return
        montant_tarif = CantineExterneService.get_tarif(id_annee)
        dialog = PensionnaireCantineDialog(montant_tarif, self)
        if not dialog.exec():
            return
        ok, message = CantineExterneService.inscrire_externe(id_annee, dialog.values())
        if not ok:
            QMessageBox.warning(self, "Cantine externe", message)
            return
        self.refresh_data()
        QMessageBox.information(self, "Inscription créée", message)

    def _supprimer(self, row):
        obstacles = CantineExterneService.get_obstacles_suppression(row["id"])
        if obstacles:
            QMessageBox.warning(
                self, "Suppression impossible",
                f"{row['nom']} ne peut pas être supprimé :\n\n  •  " + "\n  •  ".join(obstacles)
            )
            return
        if QMessageBox.question(
            self, "Supprimer le pensionnaire",
            f"Supprimer définitivement {row['nom']} de la cantine ?\n\nCette action est tracée.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        motif, ok_dialog = QInputDialog.getMultiLineText(
            self, "Supprimer le pensionnaire", "Motif de la suppression (obligatoire) :"
        )
        if not ok_dialog:
            return
        ok, message = CantineExterneService.supprimer_pensionnaire(
            row["id"], motif, id_utilisateur=AppSession.get_current_user_id()
        )
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Cantine", message)
        if ok:
            self.refresh_data()

    def _payer(self, row):
        dialog = VersementCantineDialog(row, self)
        if dialog.exec():
            self.refresh_data()
            if dialog.receipt_data:
                ReceiptPrinter.print_receipt(self, dialog.receipt_data)

    def _save_tarif(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return
        ok, message = CantineExterneService.update_tarif(id_annee, self.spin_tarif.value())
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Tarif", message)
        if ok:
            self.refresh_data()

    def _annuler_versement(self, row):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Annuler le paiement")
        dialog.setLabelText(f"Motif d’annulation du reçu {row['recu']} :")
        dialog.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput, True)
        dialog.setStyleSheet(MESSAGEBOX_STYLE)
        if dialog.exec() != QDialog.Accepted:
            return
        motif = dialog.textValue()
        ok, message = CantineExterneService.annuler_versement(row["id"], motif)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Paiement", message)
        if ok:
            self.refresh_data()
