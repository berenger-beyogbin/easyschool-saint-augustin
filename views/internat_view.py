from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QInputDialog, QSizePolicy, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from app.session import AppSession
from app.styles import (
    BUTTON_DANGER, BUTTON_PRIMARY, BUTTON_SECONDARY, BUTTON_TABLE_ACTION_PRIMARY,
    COLORS, COMBO_STYLE, INPUT_STYLE, TABLE_STYLE, TAB_STYLE,
)
from services.internat_service import InternatService
from utils.receipt_printer import ReceiptPrinter
from views.ui_components import KpiCard


def _money(value) -> str:
    return f"{int(value):,} FCFA".replace(",", " ")


class _FloatingField(QWidget):
    """Champ avec un libellé posé à cheval sur sa bordure supérieure."""

    def __init__(self, label_text: str, field: QWidget, parent=None):
        super().__init__(parent)
        self.setFixedHeight(58)
        self._border = QFrame(self)
        self._border.setObjectName("floatingFieldBorder")
        self._border.setStyleSheet(
            "QFrame#floatingFieldBorder{background:#FFFFFF;"
            "border:1px solid #CBD5E1;border-radius:8px;}"
        )
        border_layout = QHBoxLayout(self._border)
        border_layout.setContentsMargins(1, 8, 1, 1)
        border_layout.addWidget(field)
        self._label = QLabel(label_text, self)
        self._label.setStyleSheet(
            f"background:#FFFFFF;color:{COLORS['text']};padding:0 6px;"
            "border:none;font-size:12px;font-weight:700;"
        )
        self._label.adjustSize()
        self._label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._border.setGeometry(0, 8, self.width(), max(0, self.height() - 8))
        self._label.move(10, 0)


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


class DossierDialog(QDialog):
    def __init__(self, id_internat: int, parent=None):
        super().__init__(parent)
        self.id_internat = id_internat
        self.setWindowTitle("Dossier d’admission à l’internat")
        self.resize(680, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(_section_title(
            "Pièces du dossier",
            "Indiquez la quantité effectivement reçue pour chaque pièce.",
        ))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Pièce", "Demandée", "Reçue"])
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.spins = []
        for row, piece in enumerate(InternatService.get_pieces(id_internat)):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(piece["libelle"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(piece["demandee"])))
            spin = QSpinBox()
            spin.setRange(0, max(20, piece["demandee"]))
            spin.setValue(piece["recue"])
            self.table.setCellWidget(row, 2, spin)
            self.spins.append((piece["id"], spin))
        layout.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer le dossier")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        ok, message = InternatService.enregistrer_dossier(
            self.id_internat, {piece_id: spin.value() for piece_id, spin in self.spins}
        )
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Dossier", message)


class VersementDialog(QDialog):
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
        self.montant.setPlaceholderText("Ex. 100 000")
        self.montant.setStyleSheet(INPUT_STYLE)
        self.mode = QComboBox()
        self.mode.setStyleSheet(COMBO_STYLE)
        self.mode.addItems(["ESPÈCES", "MOBILE MONEY", "VIREMENT", "CHÈQUE"])
        self.reference = QLineEdit()
        self.reference.setPlaceholderText("Facultative")
        self.reference.setStyleSheet(INPUT_STYLE)
        form.addRow("Montant * :", self.montant)
        form.addRow("Mode de paiement :", self.mode)
        form.addRow("Référence :", self.reference)
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
        ok, message = InternatService.verser(
            self.pensionnaire["id"], montant, self.mode.currentText(), self.reference.text()
        )
        if ok:
            numero_recu = message.partition("Reçu ")[2].rstrip(".") or "—"
            self.receipt_data = {
                "preview_title": "Aperçu — Reçu de paiement internat",
                "receipt_title": "REÇU DE PAIEMENT — INTERNAT",
                "scol_label": "INTERNAT",
                "date": date.today().strftime("%d/%m/%Y"),
                "matricule": self.pensionnaire.get("matricule", ""),
                "nom": self.pensionnaire.get("nom", ""),
                "classe": self.pensionnaire.get("classe_externe", ""),
                "numero": numero_recu,
                "motif": "Pension internat",
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


class PensionnaireExterneDialog(QDialog):
    """Saisie minimale d'une pensionnaire scolarisée hors du collège."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle pensionnaire externe")
        self.setMinimumWidth(560)
        form = QFormLayout(self)
        self.nom = QLineEdit()
        self.prenoms = QLineEdit()
        self.date_naissance = QDateEdit(QDate.currentDate().addYears(-10))
        self.date_naissance.setCalendarPopup(True)
        self.date_naissance.setMaximumDate(QDate.currentDate())
        self.lieu_naissance = QLineEdit()
        self.habitation = QLineEdit()
        self.etablissement = QLineEdit()
        self.classe = QLineEdit()
        self.responsable_nom = QLineEdit()
        self.responsable_contact = QLineEdit()
        for field in (
            self.nom, self.prenoms, self.lieu_naissance, self.habitation,
            self.etablissement, self.classe, self.responsable_nom,
            self.responsable_contact,
        ):
            field.setStyleSheet(INPUT_STYLE)
        self.etablissement.setPlaceholderText("École primaire fréquentée")
        self.classe.setPlaceholderText("Ex. CM1")
        self.responsable_contact.setPlaceholderText("Téléphone")
        form.addRow("Nom * :", self.nom)
        form.addRow("Prénoms * :", self.prenoms)
        form.addRow("Date de naissance * :", self.date_naissance)
        form.addRow("Lieu de naissance :", self.lieu_naissance)
        form.addRow("Habitation :", self.habitation)
        form.addRow("École fréquentée * :", self.etablissement)
        form.addRow("Classe fréquentée * :", self.classe)
        form.addRow("Responsable légal * :", self.responsable_nom)
        form.addRow("Contact du responsable * :", self.responsable_contact)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Créer et inscrire")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _validate(self):
        required = (
            self.nom, self.prenoms, self.etablissement, self.classe,
            self.responsable_nom, self.responsable_contact,
        )
        if any(not field.text().strip() for field in required):
            QMessageBox.warning(self, "Pensionnaire externe", "Renseignez tous les champs marqués d’un astérisque.")
            return
        self.accept()

    def values(self):
        qdate = self.date_naissance.date()
        return {
            "nom": self.nom.text(), "prenoms": self.prenoms.text(),
            "date_naissance": date(qdate.year(), qdate.month(), qdate.day()),
            "lieu_naissance": self.lieu_naissance.text(),
            "habitation": self.habitation.text(),
            "etablissement": self.etablissement.text(), "classe": self.classe.text(),
            "responsable_nom": self.responsable_nom.text(),
            "responsable_contact": self.responsable_contact.text(),
        }


class InternatView(QWidget):
    TAB_DASHBOARD = 0
    TAB_PENSIONNAIRES = 1
    TAB_PAIEMENTS = 2
    TAB_TARIFS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._payment_rows = []
        self._tariff_editors = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        title = QLabel("INTERNAT FILLES D’ATTINGUIÉ")
        title.setStyleSheet(f"font-size:22px; font-weight:800; color:{COLORS['primary_dark']};")
        subtitle = QLabel("Inscrire une pensionnaire, compléter son dossier, encaisser et suivre son solde")
        subtitle.setStyleSheet(f"color:{COLORS['muted']}; margin-bottom:8px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        journey = QLabel("1  Inscrire l’élève    →    2  Compléter le dossier    →    3  Encaisser    →    4  Suivre le solde")
        journey.setStyleSheet(
            f"color:{COLORS['primary_dark']}; padding:5px 2px 9px 2px; font-weight:600;"
        )
        root.addWidget(journey)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._build_dashboard(), "Vue d’ensemble")
        self.tabs.addTab(self._build_pensionnaires(), "Pensionnaires")
        self.tabs.addTab(self._build_payments(), "Paiements")
        self.tabs.addTab(self._build_tarifs(), "Tarifs et échéances")
        self.tabs.currentChanged.connect(lambda _: self.refresh_data())
        root.addWidget(self.tabs)

    def _build_dashboard(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)

        actions = QHBoxLayout()
        actions.addWidget(_section_title(
            "Que souhaitez-vous faire ?",
            "Commencez une admission ou enregistrez directement un paiement.",
        ), 1)
        btn_register = QPushButton("+ Inscrire une pensionnaire")
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
            ("admises", "Admises", COLORS["success"]),
            ("dossiers_incomplets", "Dossiers à compléter", COLORS["warning"]),
            ("attendu", "Pension attendue", COLORS["purple"]),
            ("encaisse", "Pension encaissée", COLORS["success"]),
            ("reste", "Reste à recouvrer", COLORS["danger"]),
        ]
        for index, (key, label, color) in enumerate(specs):
            card = KpiCard(label, color)
            self.cards[key] = card
            (row1 if index < 3 else row2).addWidget(card)
        layout.addLayout(row1)
        layout.addLayout(row2)

        action_frame = QFrame()
        action_frame.setStyleSheet("QFrame{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;}")
        action_layout = QVBoxLayout(action_frame)
        action_layout.addWidget(QLabel("Actions à effectuer"))
        self.lbl_next_actions = QLabel("Chargement…")
        self.lbl_next_actions.setWordWrap(True)
        self.lbl_next_actions.setStyleSheet(f"color:{COLORS['muted']}; border:none;")
        action_layout.addWidget(self.lbl_next_actions)
        layout.addWidget(action_frame)
        layout.addStretch()
        return widget

    def _build_pensionnaires(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.addWidget(_section_title(
            "Inscrire et suivre les pensionnaires",
            "Sélectionnez une élève du collège ou créez la fiche d’une pensionnaire scolarisée ailleurs.",
        ))

        form_frame = QFrame()
        form_frame.setObjectName("internatAdmissionForm")
        form_frame.setStyleSheet(
            "QFrame#internatAdmissionForm{background:#FFFFFF;"
            "border:1px solid #E2E8F0;border-radius:12px;}"
        )
        form = QHBoxLayout(form_frame)
        form.setContentsMargins(16, 14, 16, 14)
        form.setSpacing(18)
        self.cmb_origine = QComboBox()
        compact_combo_style = COMBO_STYLE + """
            QComboBox, QComboBox:focus {
                border:none; border-radius:7px; background:#FFFFFF;
                padding:6px 10px;
            }
            QComboBox::drop-down {
                width:32px; border-left:1px solid #E2E8F0;
                background:#F8FAFC; border-radius:0 7px 7px 0;
            }
        """
        self.cmb_origine.setStyleSheet(compact_combo_style)
        self.cmb_origine.addItem("Élève du collège", "COLLEGE")
        self.cmb_origine.addItem("Pensionnaire externe", "EXTERNE")
        self.cmb_origine.currentIndexChanged.connect(self._origine_changed)
        self.cmb_eleve = QComboBox()
        self.cmb_eleve.setMinimumWidth(0)
        self.cmb_eleve.setStyleSheet(compact_combo_style)
        self.cmb_type = QComboBox()
        self.cmb_type.setStyleSheet(compact_combo_style)
        self.cmb_type.addItem("Nouvelle inscription", "NOUVELLE")
        self.cmb_type.addItem("Renouvellement", "ANCIENNE")
        self.date_debut = QDateEdit(QDate.currentDate())
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setStyleSheet("""
            QDateEdit, QDateEdit:focus {
                border:none; border-radius:7px; background:#FFFFFF;
                padding:6px 10px;
            }
            QDateEdit::drop-down {
                width:30px; border-left:1px solid #E2E8F0;
                background:#F8FAFC;
            }
        """)
        btn = QPushButton("Confirmer")
        btn.setStyleSheet(BUTTON_PRIMARY)
        btn.setFixedHeight(50)
        btn.setMinimumWidth(150)
        btn.clicked.connect(self._inscrire)
        origine_field = _FloatingField("1. Origine", self.cmb_origine)
        eleve_field = _FloatingField("2. Élève", self.cmb_eleve)
        type_field = _FloatingField("3. Type", self.cmb_type)
        date_field = _FloatingField("4. Date d’entrée", self.date_debut)
        origine_field.setMinimumWidth(180)
        eleve_field.setMinimumWidth(320)
        type_field.setMinimumWidth(210)
        date_field.setMinimumWidth(180)
        for field in (origine_field, eleve_field, type_field, date_field):
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form.addWidget(origine_field, 2)
        form.addWidget(eleve_field, 5)
        form.addWidget(type_field, 2)
        form.addWidget(date_field, 2)
        form.addWidget(btn, 0, Qt.AlignBottom)
        layout.addWidget(form_frame)

        filters = QHBoxLayout()
        self.search_pensionnaire = QLineEdit()
        self.search_pensionnaire.setPlaceholderText("Rechercher par nom ou matricule…")
        self.search_pensionnaire.setStyleSheet(INPUT_STYLE)
        self.search_pensionnaire.setFixedHeight(38)
        self.search_pensionnaire.textChanged.connect(self._filter_pensionnaires)
        self.filter_status = QComboBox()
        self.filter_status.setStyleSheet(COMBO_STYLE)
        self.filter_status.addItem("Tous les statuts", "")
        self.filter_status.addItem("Dossiers à compléter", "DOSSIER_INCOMPLET")
        self.filter_status.addItem("Paiement attendu", "EN_ATTENTE_PAIEMENT")
        self.filter_status.addItem("Admises", "ADMISE")
        self.filter_status.setFixedHeight(38)
        self.filter_status.currentIndexChanged.connect(self._filter_pensionnaires)
        filters.addWidget(self.search_pensionnaire, 1)
        filters.addWidget(self.filter_status)
        layout.addLayout(filters)

        self.table_pensionnaires = QTableWidget(0, 8)
        self.table_pensionnaires.setHorizontalHeaderLabels([
            "Matricule", "Nom et prénoms", "Type", "Prochaine action",
            "Pension", "Versé", "Reste", "Actions",
        ])
        self.table_pensionnaires.setStyleSheet(TABLE_STYLE)
        self.table_pensionnaires.setAlternatingRowColors(True)
        self.table_pensionnaires.verticalHeader().setDefaultSectionSize(44)
        self.table_pensionnaires.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_pensionnaires.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_pensionnaires.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        layout.addWidget(self.table_pensionnaires)
        return widget

    def _build_payments(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(_section_title(
            "Historique des paiements",
            "Consultez les reçus et les annulations de la pension annuelle.",
        ), 1)
        new_payment = QPushButton("+ Nouveau paiement")
        new_payment.setStyleSheet(BUTTON_PRIMARY)
        new_payment.clicked.connect(self._choose_pensionnaire_to_pay)
        header.addWidget(new_payment)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.search_payment = QLineEdit()
        self.search_payment.setPlaceholderText("Rechercher un reçu ou une pensionnaire…")
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

    def _build_tarifs(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(_section_title(
            "Tarifs et échéances",
            "Ces montants s’appliqueront uniquement aux prochaines inscriptions.",
        ), 1)
        self.btn_save_tariffs = QPushButton("Enregistrer les modifications")
        self.btn_save_tariffs.setStyleSheet(BUTTON_PRIMARY)
        self.btn_save_tariffs.clicked.connect(self._save_all_tarifs)
        header.addWidget(self.btn_save_tariffs)
        layout.addLayout(header)

        self.table_tarifs = QTableWidget(0, 4)
        self.table_tarifs.setObjectName("internatTariffs")
        self.table_tarifs.setHorizontalHeaderLabels([
            "Échéance", "Nouvelle inscription", "Renouvellement", "Date limite",
        ])
        self.table_tarifs.setStyleSheet(TABLE_STYLE + f"""
            QTableWidget#internatTariffs {{
                border: none;
                gridline-color: transparent;
                background: transparent;
            }}
            QTableWidget#internatTariffs QHeaderView::section {{
                border-right: none;
                border-bottom: 1px solid {COLORS['border_soft']};
            }}
            QTableWidget#internatTariffs QSpinBox,
            QTableWidget#internatTariffs QDateEdit {{
                border: none;
                background: transparent;
                padding: 4px 6px;
            }}
            QTableWidget#internatTariffs QSpinBox:focus,
            QTableWidget#internatTariffs QDateEdit:focus {{
                border: none;
                background: #EEF4FF;
            }}
            QTableWidget#internatTariffs QSpinBox::up-button,
            QTableWidget#internatTariffs QSpinBox::down-button,
            QTableWidget#internatTariffs QDateEdit::drop-down {{
                border: none;
                background: transparent;
            }}
        """)
        self.table_tarifs.setAlternatingRowColors(True)
        self.table_tarifs.verticalHeader().setDefaultSectionSize(48)
        self.table_tarifs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in (1, 2, 3):
            self.table_tarifs.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        layout.addWidget(self.table_tarifs)

        totals = QHBoxLayout()
        totals.addStretch()
        self.lbl_total_new = QLabel("Total nouvelle inscription : 0 FCFA")
        self.lbl_total_old = QLabel("Total renouvellement : 0 FCFA")
        for label in (self.lbl_total_new, self.lbl_total_old):
            label.setStyleSheet(
                f"background:#EEF4FF; color:{COLORS['primary_dark']}; padding:10px 14px;"
                "border-radius:8px; font-weight:700;"
            )
            totals.addWidget(label)
        layout.addLayout(totals)
        return widget

    def refresh_data(self):
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return
        stats = InternatService.dashboard(id_annee)
        for key, card in self.cards.items():
            value = stats[key]
            card.set_value(_money(value) if key in {"attendu", "encaisse", "reste"} else str(value))
        self.lbl_next_actions.setText(
            f"• {stats['dossiers_incomplets']} dossier(s) à compléter\n"
            f"• {_money(stats['reste'])} restant à recouvrer"
        )
        self._rows = InternatService.get_pensionnaires(id_annee)
        self._load_eligibles(id_annee)
        self._filter_pensionnaires()
        self._payment_rows = InternatService.get_versements(id_annee)
        self._filter_payments()
        self._load_tarifs(id_annee)

    load_data = refresh_data

    def _load_eligibles(self, id_annee):
        previous = self.cmb_eleve.currentData()
        self.cmb_eleve.clear()
        self.cmb_eleve.addItem("Sélectionner une élève inscrite…", None)
        for row in InternatService.get_eleves_eligibles(id_annee):
            self.cmb_eleve.addItem(f"{row['matricule']} — {row['nom']}", row["id_inscription"])
        if previous is not None:
            index = self.cmb_eleve.findData(previous)
            if index >= 0:
                self.cmb_eleve.setCurrentIndex(index)

    def _origine_changed(self, *_):
        externe = self.cmb_origine.currentData() == "EXTERNE"
        self.cmb_eleve.setEnabled(not externe)
        self.cmb_eleve.setToolTip(
            "La fiche sera créée sans inscription scolaire au collège."
            if externe else "Sélectionnez une élève inscrite au collège."
        )

    @staticmethod
    def _next_action(row):
        if row["statut"] == "DOSSIER_INCOMPLET":
            return "Compléter le dossier"
        if row["statut"] == "EN_ATTENTE_PAIEMENT":
            return "Enregistrer le 1er paiement"
        if row["reste"] <= 0:
            return "Pension soldée"
        if row["statut"] == "ADMISE":
            return "Suivre les échéances"
        return row["statut"].replace("_", " ").title()

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
                row["matricule"], row["nom"],
                ("Externe · " if row.get("origine") == "EXTERNE" else "Collège · ")
                + ("Nouvelle" if row["type"] == "NOUVELLE" else "Renouvellement"),
                self._next_action(row), _money(row["montant"]),
                _money(row["verse"]), _money(row["reste"]),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col in (4, 5, 6):
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
            table.setCellWidget(i, 7, actions)

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

    def _load_tarifs(self, id_annee):
        rows = InternatService.get_echeances(id_annee)
        self._tariff_editors = []
        self.table_tarifs.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table_tarifs.setItem(i, 0, QTableWidgetItem(row.Libelle))
            new = QSpinBox()
            new.setRange(0, 10_000_000)
            new.setSingleStep(5_000)
            new.setSuffix(" FCFA")
            new.setValue(int(row.MontantNouvelle))
            old = QSpinBox()
            old.setRange(0, 10_000_000)
            old.setSingleStep(5_000)
            old.setSuffix(" FCFA")
            old.setValue(int(row.MontantAncienne))
            due = QDateEdit()
            due.setDisplayFormat("dd/MM/yyyy")
            due.setCalendarPopup(True)
            due.setSpecialValueText("À définir")
            due.setMinimumDate(QDate(2000, 1, 1))
            due.setDate(
                QDate(row.DateLimite.year, row.DateLimite.month, row.DateLimite.day)
                if row.DateLimite else QDate(2000, 1, 1)
            )
            new.valueChanged.connect(self._update_tariff_totals)
            old.valueChanged.connect(self._update_tariff_totals)
            self.table_tarifs.setCellWidget(i, 1, new)
            self.table_tarifs.setCellWidget(i, 2, old)
            self.table_tarifs.setCellWidget(i, 3, due)
            self._tariff_editors.append((row.IDEcheance, new, old, due))
        self._update_tariff_totals()

    def _update_tariff_totals(self, *_):
        total_new = sum(new.value() for _, new, _, _ in self._tariff_editors)
        total_old = sum(old.value() for _, _, old, _ in self._tariff_editors)
        self.lbl_total_new.setText(f"Total nouvelle inscription : {_money(total_new)}")
        self.lbl_total_old.setText(f"Total renouvellement : {_money(total_old)}")

    def _go_to_registration(self):
        self.tabs.setCurrentIndex(self.TAB_PENSIONNAIRES)
        self.cmb_eleve.setFocus()

    def _go_to_payment(self):
        self.tabs.setCurrentIndex(self.TAB_PAIEMENTS)
        self._choose_pensionnaire_to_pay()

    def _choose_pensionnaire_to_pay(self):
        candidates = [row for row in self._rows if row["reste"] > 0]
        if not candidates:
            QMessageBox.information(self, "Paiement", "Aucune pensionnaire n’a de solde à payer.")
            return
        labels = [f"{row['matricule']} — {row['nom']} — reste {_money(row['reste'])}" for row in candidates]
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Nouveau paiement")
        dialog.setLabelText("Sélectionnez la pensionnaire :")
        dialog.setComboBoxItems(labels)
        dialog.setComboBoxEditable(False)
        dialog.setStyleSheet(f"""
            QInputDialog QPushButton {{
                min-width:110px; min-height:38px; padding:6px 18px;
                border:1px solid {COLORS['border']}; border-radius:7px;
                background:#FFFFFF; color:{COLORS['text']}; font-weight:600;
            }}
            QInputDialog QPushButton:default {{
                background:{COLORS['primary']}; color:#FFFFFF;
                border-color:{COLORS['primary']};
            }}
            QInputDialog QPushButton:default:hover {{
                background:{COLORS['primary_dark']}; color:#FFFFFF;
            }}
        """)
        buttons = dialog.findChild(QDialogButtonBox)
        if buttons is not None:
            ok_button = buttons.button(QDialogButtonBox.Ok)
            if ok_button is not None:
                ok_button.setText("Valider")
        combo = dialog.findChild(QComboBox)
        if combo is not None:
            combo.setStyleSheet(COMBO_STYLE + f"""
                QComboBox QAbstractItemView::item:hover,
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {COLORS['selection']};
                    color: {COLORS['text']};
                }}
            """)
        if dialog.exec() == QDialog.Accepted:
            selected = dialog.textValue()
            self._payer(candidates[labels.index(selected)])

    def _inscrire(self):
        qdate = self.date_debut.date()
        date_debut = date(qdate.year(), qdate.month(), qdate.day())
        if self.cmb_origine.currentData() == "EXTERNE":
            dialog = PensionnaireExterneDialog(self)
            if not dialog.exec():
                return
            id_annee = AppSession.get_active_annee_id()
            ok, message = InternatService.inscrire_externe(
                id_annee, dialog.values(), self.cmb_type.currentData(), date_debut,
            )
            if not ok:
                QMessageBox.warning(self, "Internat", message)
                return
            self.refresh_data()
            QMessageBox.information(self, "Inscription créée", message)
            return
        if not self.cmb_eleve.currentData():
            QMessageBox.warning(self, "Internat", "Sélectionnez une élève avant de continuer.")
            self.cmb_eleve.setFocus()
            return
        selected_matricule = self.cmb_eleve.currentText().split(" — ", 1)[0]
        ok, message = InternatService.inscrire(
            self.cmb_eleve.currentData(), self.cmb_type.currentData(),
            date_debut,
        )
        if not ok:
            QMessageBox.warning(self, "Internat", message)
            return
        self.refresh_data()
        created = next((row for row in self._rows if row["matricule"] == selected_matricule), None)
        box = QMessageBox(self)
        box.setWindowTitle("Inscription créée")
        box.setIcon(QMessageBox.Information)
        box.setText(message)
        box.setInformativeText("Prochaine étape : compléter le dossier d’admission.")
        complete = box.addButton("Compléter le dossier", QMessageBox.AcceptRole)
        box.addButton("Plus tard", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() == complete and created:
            self._dossier(created)

    def _dossier(self, row):
        if DossierDialog(row["id"], self).exec():
            self.refresh_data()

    def _payer(self, row):
        dialog = VersementDialog(row, self)
        if dialog.exec():
            self.refresh_data()
            if dialog.receipt_data:
                ReceiptPrinter.print_receipt(self, dialog.receipt_data)

    def _save_all_tarifs(self):
        for row_id, nouvelle, ancienne, due in self._tariff_editors:
            qdate = due.date()
            date_limite = None if qdate == QDate(2000, 1, 1) else date(
                qdate.year(), qdate.month(), qdate.day()
            )
            ok, message = InternatService.update_echeance(
                row_id, nouvelle.value(), ancienne.value(), date_limite
            )
            if not ok:
                QMessageBox.warning(self, "Tarifs", message)
                return
        QMessageBox.information(self, "Tarifs", "Toutes les modifications ont été enregistrées.")
        self.refresh_data()

    def _annuler_versement(self, row):
        motif, ok_dialog = QInputDialog.getMultiLineText(
            self, "Annuler le paiement", f"Motif d’annulation du reçu {row['recu']} :"
        )
        if not ok_dialog:
            return
        ok, message = InternatService.annuler_versement(row["id"], motif)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Paiement", message)
        if ok:
            self.refresh_data()
