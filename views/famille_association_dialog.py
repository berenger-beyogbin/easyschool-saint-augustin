"""Saisie simple des contacts père, mère et tuteur depuis la fiche élève."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QRadioButton, QVBoxLayout,
)

from app.styles import COLORS, COMBO_STYLE, INPUT_STYLE
from services.famille_service import FamilleService


class FamilleAssociationDialog(QDialog):
    """Masque la notion technique de famille et saisit directement les contacts."""

    def __init__(self, parent=None, id_eleve: int | None = None, eleve_label: str = "", famille=None):
        super().__init__(parent)
        self.id_eleve = id_eleve
        self.id_famille_choisie = None
        self._famille = famille
        self._fields = {}
        self._contact_configs = {}
        self._suggestion_boxes = {}
        self._existing_family_id = None
        self._applying_suggestion = False
        self.setWindowTitle("Contacts des parents")
        self.resize(980, 470)
        self._init_ui(eleve_label)
        self._prefill()

    def _init_ui(self, eleve_label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Renseigner les contacts des parents")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['primary_dark']};")
        layout.addWidget(title)
        if eleve_label:
            student = QLabel(f"Élève : {eleve_label}")
            student.setStyleSheet(f"font-size: 12px; color: {COLORS['muted']};")
            layout.addWidget(student)

        hint = QLabel(
            "Saisissez au moins le nom et le téléphone d'une personne, puis choisissez-la comme contact principal."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.principal_group = QButtonGroup(self)
        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(self._contact_card(
            "PÈRE", "PERE", "NomPere", "TelPere", "TelBureauPere", "EmailPere"
        ))
        cards.addWidget(self._contact_card(
            "MÈRE", "MERE", "NomMere", "TelMere", "TelBureauMere", "EmailMere"
        ))
        cards.addWidget(self._contact_card(
            "TUTEUR", "TUTEUR", "NomTuteur", "CelTuteur", "TelBureauTuteur", "EmailTuteur"
        ))
        layout.addLayout(cards, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer les contacts")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _contact_card(self, title, principal_value, nom_key, mobile_key, phone2_key, email_key):
        box = QGroupBox(title)
        box.setStyleSheet(
            f"QGroupBox {{ font-weight: 800; color: {COLORS['text']}; border: 1px solid {COLORS['border']};"
            "border-radius: 8px; margin-top: 10px; padding: 12px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
        )
        form = QFormLayout(box)
        radio = QRadioButton("Contact principal")
        radio.setProperty("principal_value", principal_value)
        self.principal_group.addButton(radio)
        form.addRow(radio)
        suggestion = QComboBox()
        suggestion.setStyleSheet(COMBO_STYLE)
        suggestion.setToolTip("Sélectionnez un parent existant pour précharger ses coordonnées.")
        suggestion.setVisible(False)
        suggestion.activated.connect(lambda index, role=principal_value: self._apply_suggestion(role, index))
        self._suggestion_boxes[principal_value] = suggestion
        form.addRow(suggestion)
        for label, key, placeholder in (
            ("Nom et prénoms", nom_key, "Nom complet"),
            ("Téléphone principal", mobile_key, "Ex : 0700000000"),
            ("Deuxième téléphone", phone2_key, "Facultatif"),
            ("E-mail", email_key, "Facultatif"),
        ):
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setStyleSheet(INPUT_STYLE)
            self._fields[key] = field
            form.addRow(label, field)
        self._contact_configs[principal_value] = (nom_key, mobile_key, phone2_key, email_key)
        self._fields[nom_key].textChanged.connect(
            lambda _text, role=principal_value: self._schedule_contact_search(role)
        )
        self._fields[mobile_key].textChanged.connect(
            lambda _text, role=principal_value: self._schedule_contact_search(role)
        )
        return box

    def _schedule_contact_search(self, role: str):
        if self._applying_suggestion:
            return
        name_key, phone_key, _, _ = self._contact_configs[role]
        name = self._fields[name_key].text().strip()
        phone = self._fields[phone_key].text().strip()
        digits = "".join(character for character in phone if character.isdigit())
        query = phone if len(digits) >= 6 else name
        if len(name) < 3 and len(digits) < 6:
            self._suggestion_boxes[role].setVisible(False)
            return
        QTimer.singleShot(300, lambda: self._refresh_suggestions(role, query, name, phone))

    def _refresh_suggestions(self, role: str, query: str, expected_name: str, expected_phone: str):
        name_key, phone_key, _, _ = self._contact_configs[role]
        if (self._fields[name_key].text().strip() != expected_name
                or self._fields[phone_key].text().strip() != expected_phone):
            return
        matches = FamilleService.search_parent_contacts(query)
        combo = self._suggestion_boxes[role]
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Parent existant trouvé — sélectionner…", None)
        for match in matches:
            children = f" · Enfant(s) : {match['children']}" if match["children"] else ""
            combo.addItem(
                f"{match['role']} · {match['name']} · {match['phone']}{children}",
                match,
            )
        combo.setCurrentIndex(0)
        combo.blockSignals(False)
        combo.setVisible(bool(matches))

    def _apply_suggestion(self, role: str, index: int):
        match = self._suggestion_boxes[role].itemData(index)
        if not match:
            return
        self._applying_suggestion = True
        try:
            for key, value in match["contacts"].items():
                if key in self._fields:
                    self._fields[key].setText(value or "")
            self._existing_family_id = match["family_id"]
            for combo in self._suggestion_boxes.values():
                combo.setVisible(False)
        finally:
            self._applying_suggestion = False

    def _prefill(self):
        famille = self._famille
        if not famille:
            return
        for key, field in self._fields.items():
            field.setText(getattr(famille, key, None) or "")
        principal = {1: "TUTEUR", 2: "PERE", 3: "MERE"}.get(famille.QualiteResponsable)
        for button in self.principal_group.buttons():
            if button.property("principal_value") == principal:
                button.setChecked(True)
                break

    def _save(self):
        checked = self.principal_group.checkedButton()
        data = {key: field.text().strip() for key, field in self._fields.items()}
        data["Principal"] = checked.property("principal_value") if checked else None
        data["ExistingFamilyId"] = self._existing_family_id
        ok, message, id_famille = FamilleService.enregistrer_contacts_eleve(self.id_eleve, data)
        if not ok:
            QMessageBox.warning(self, "Contacts incomplets", message)
            return
        self.id_famille_choisie = id_famille
        QMessageBox.information(self, "Contacts enregistrés", message)
        self.accept()
