from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QCheckBox, QScrollArea, QFrame, QMessageBox, QSizePolicy,
)

from app.styles import COLORS, COMBO_STYLE, configure_button


# ===========================================================================
# Onglet 3 : Administration des droits par profil
# ===========================================================================

class _DroitsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}  # code → checkbox
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # En-tête : sélecteur de profil + bouton enregistrer
        top = QHBoxLayout()
        lbl = QLabel("Profil sélectionné :")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; font-weight: 600;")
        self.cmb_profil = QComboBox()
        self.cmb_profil.setStyleSheet(COMBO_STYLE)
        self.cmb_profil.setFixedHeight(36)
        self.cmb_profil.setMinimumWidth(220)
        self._load_profils_combo()
        self.cmb_profil.currentIndexChanged.connect(self._on_profil_changed)

        self.btn_save = QPushButton("Enregistrer les droits")
        configure_button(self.btn_save, "success", fixed_height=36, min_width=160)
        self.btn_save.clicked.connect(self._on_save)

        top.addWidget(lbl)
        top.addWidget(self.cmb_profil)
        top.addSpacing(16)
        top.addWidget(self.btn_save)
        top.addStretch()
        layout.addLayout(top)

        # Note pour les super-admins
        self.lbl_admin_note = QLabel(
            "⚑  Ce profil est Super-administrateur : il dispose automatiquement de tous les droits."
        )
        self.lbl_admin_note.setStyleSheet(
            f"color: {COLORS['danger']}; font-size: 12px; font-weight: 600;"
            "background-color: transparent; padding: 4px 0;"
        )
        self.lbl_admin_note.setVisible(False)
        layout.addWidget(self.lbl_admin_note)

        # Zone scrollable : matrice des permissions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}")

        self.matrix_widget = QWidget()
        self.matrix_widget.setStyleSheet(f"background-color: {COLORS['card']};")
        self.matrix_layout = QVBoxLayout(self.matrix_widget)
        self.matrix_layout.setContentsMargins(20, 16, 20, 16)
        self.matrix_layout.setSpacing(0)

        scroll.setWidget(self.matrix_widget)
        layout.addWidget(scroll, 1)

        self._build_matrix()
        self._on_profil_changed()

    def _load_profils_combo(self):
        from services.profil_service import ProfilService
        self.cmb_profil.blockSignals(True)
        self.cmb_profil.clear()
        for p in ProfilService.get_all():
            self.cmb_profil.addItem(p.Libelle, p.IDProfil)
        self.cmb_profil.blockSignals(False)

    def _build_matrix(self):
        from services.permission_service import PermissionService
        # Vider la matrice actuelle
        while self.matrix_layout.count():
            item = self.matrix_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        by_module = PermissionService.get_by_module()
        first = True
        for module, perms in by_module.items():
            if not first:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"color: {COLORS['border']}; margin: 6px 0;")
                self.matrix_layout.addWidget(sep)
            first = False

            # En-tête du module
            lbl_mod = QLabel(f"  {module}")
            lbl_mod.setStyleSheet(
                f"color: {COLORS['primary_dark']}; font-size: 13px; font-weight: 700;"
                f"background-color: {COLORS['bg']}; border-radius: 4px; padding: 6px 10px;"
                "margin: 4px 0;"
            )
            self.matrix_layout.addWidget(lbl_mod)

            # Permissions du module
            for perm in perms:
                row_widget = QWidget()
                row_widget.setStyleSheet("background-color: transparent;")
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(20, 2, 8, 2)
                row_layout.setSpacing(12)

                cb = QCheckBox(perm.Libelle)
                cb.setStyleSheet(
                    f"QCheckBox {{ color: {COLORS['text']}; font-size: 13px; }}"
                    f"QCheckBox::indicator {{"
                    f"  width: 18px; height: 18px;"
                    f"  border: 2px solid {COLORS['input_border']};"
                    f"  border-radius: 4px;"
                    f"  background-color: {COLORS['surface']};"
                    f"}}"
                    f"QCheckBox::indicator:checked {{"
                    f"  background-color: {COLORS['primary']};"
                    f"  border-color: {COLORS['primary']};"
                    f"}}"
                    f"QCheckBox::indicator:hover {{"
                    f"  border-color: {COLORS['primary']};"
                    f"}}"
                )
                cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self._checkboxes[perm.Code] = cb

                lbl_code = QLabel(f"[{perm.Code}]")
                lbl_code.setStyleSheet(
                    f"color: {COLORS['muted']}; font-size: 11px; font-family: monospace;"
                )
                lbl_code.setFixedWidth(220)

                row_layout.addWidget(cb, 1)
                row_layout.addWidget(lbl_code)
                self.matrix_layout.addWidget(row_widget)

        self.matrix_layout.addStretch()

    def load_data(self):
        self._load_profils_combo()
        self._build_matrix()
        self._on_profil_changed()

    def _on_profil_changed(self):
        from services.profil_service import ProfilService
        id_profil = self.cmb_profil.currentData()
        if not id_profil:
            return

        profil = ProfilService.get_by_id(id_profil)
        is_admin = profil.IsAdmin if profil else False

        self.lbl_admin_note.setVisible(is_admin)
        granted = ProfilService.get_profil_permissions(id_profil)

        for code, cb in self._checkboxes.items():
            cb.setChecked(code in granted or is_admin)
            cb.setEnabled(not is_admin)

    def _on_save(self):
        from services.profil_service import ProfilService
        id_profil = self.cmb_profil.currentData()
        if not id_profil:
            return
        profil = ProfilService.get_by_id(id_profil)
        if profil and profil.IsAdmin:
            QMessageBox.information(
                self, "Super-admin",
                "Les super-administrateurs disposent de tous les droits automatiquement.\n"
                "Aucune modification n'est nécessaire."
            )
            return
        codes = {code for code, cb in self._checkboxes.items() if cb.isChecked()}
        ok, msg = ProfilService.set_profil_permissions(id_profil, codes)
        if ok:
            QMessageBox.information(self, "Succès", msg)
        else:
            QMessageBox.warning(self, "Erreur", msg)
