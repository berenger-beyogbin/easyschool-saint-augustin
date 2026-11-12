from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThread, QTime, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from app.styles import BUTTON_PRIMARY, BUTTON_SECONDARY, COLORS, INPUT_STYLE
from app.session import AppSession
from services.backup_service import (
    BackupError,
    BackupSettings,
    delete_scheduled_task,
    find_pg_dump,
    load_settings,
    load_status,
    register_scheduled_task,
    run_backup,
    save_settings,
    validate_settings,
)


class _BackupWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, settings: BackupSettings, parent=None):
        super().__init__(parent)
        self.settings = settings

    def run(self):
        try:
            self.succeeded.emit(run_backup(self.settings))
        except Exception as exc:
            self.failed.emit(str(exc))


class BackupView(QWidget):
    """Paramétrage de la sauvegarde périodique de la base PostgreSQL."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: _BackupWorker | None = None
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(16)

        title = QLabel("Sauvegarde de la base de données")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['text']};")
        root.addWidget(title)

        info = QLabel(
            "Les copies sont créées dans un fichier de sauvegarde PostgreSQL compressé (.backup). "
            "Choisissez de préférence un disque externe, un NAS ou un dossier cloud synchronisé."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS['muted']}; font-size: 13px;")
        root.addWidget(info)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}"
            "QLabel { border: none; background: transparent; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        folder_row = QWidget()
        folder_row.setStyleSheet("background: transparent; border: none;")
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_edit = QLineEdit()
        self.folder_edit.setStyleSheet(INPUT_STYLE)
        self.folder_edit.setPlaceholderText("Ex. D:\\Sauvegardes\\EasySchool")
        folder_layout.addWidget(self.folder_edit, 1)
        self.browse_button = QPushButton("Choisir…")
        self.browse_button.setStyleSheet(BUTTON_SECONDARY)
        self.browse_button.clicked.connect(self._choose_folder)
        folder_layout.addWidget(self.browse_button)
        form.addRow("Dossier de destination :", folder_row)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFixedWidth(130)
        self.time_edit.setStyleSheet(INPUT_STYLE)
        form.addRow("Heure quotidienne :", self.time_edit)

        self.keep_spin = QSpinBox()
        self.keep_spin.setRange(1, 365)
        self.keep_spin.setSuffix(" copies")
        self.keep_spin.setFixedWidth(130)
        self.keep_spin.setStyleSheet(INPUT_STYLE)
        form.addRow("Conservation :", self.keep_spin)

        self.enabled_check = QCheckBox("Activer la sauvegarde automatique quotidienne")
        form.addRow("", self.enabled_check)
        card_layout.addLayout(form)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Enregistrer la planification")
        self.save_button.setStyleSheet(BUTTON_PRIMARY)
        self.save_button.clicked.connect(self._save_schedule)
        buttons.addWidget(self.save_button)

        self.backup_button = QPushButton("Sauvegarder maintenant")
        self.backup_button.setStyleSheet(BUTTON_SECONDARY)
        self.backup_button.clicked.connect(self._backup_now)
        buttons.addWidget(self.backup_button)

        self.open_button = QPushButton("Ouvrir le dossier")
        self.open_button.setStyleSheet(BUTTON_SECONDARY)
        self.open_button.clicked.connect(self._open_folder)
        buttons.addWidget(self.open_button)
        buttons.addStretch()
        card_layout.addLayout(buttons)
        root.addWidget(card)

        self.tool_label = QLabel()
        self.tool_label.setWordWrap(True)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        root.addWidget(self.tool_label)
        root.addWidget(self.status_label)

        if not AppSession.has_permission("PARAMETRES_MODIFIER"):
            for control in (
                self.folder_edit,
                self.browse_button,
                self.time_edit,
                self.keep_spin,
                self.enabled_check,
                self.save_button,
                self.backup_button,
            ):
                control.setEnabled(False)
            restricted = QLabel("Seul un administrateur autorisé peut modifier ou lancer les sauvegardes.")
            restricted.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
            root.addWidget(restricted)
        root.addStretch()

    def _settings_from_form(self) -> BackupSettings:
        return BackupSettings(
            backup_dir=self.folder_edit.text().strip(),
            enabled=self.enabled_check.isChecked(),
            schedule_time=self.time_edit.time().toString("HH:mm"),
            keep_last=self.keep_spin.value(),
        )

    def refresh_data(self):
        settings = load_settings()
        self.folder_edit.setText(settings.backup_dir)
        parsed_time = QTime.fromString(settings.schedule_time, "HH:mm")
        self.time_edit.setTime(parsed_time if parsed_time.isValid() else QTime(20, 0))
        self.keep_spin.setValue(settings.keep_last)
        self.enabled_check.setChecked(settings.enabled)

        pg_dump = find_pg_dump()
        if pg_dump:
            self.tool_label.setText(f"Outil PostgreSQL détecté : {pg_dump}")
            self.tool_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        else:
            self.tool_label.setText("Attention : pg_dump est introuvable sur ce poste.")
            self.tool_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")

        status = load_status()
        if status:
            when = status.get("completed_at", "")
            message = status.get("message", "")
            file_path = status.get("file_path", "")
            detail = f"Dernière exécution ({when}) : {message}"
            if file_path:
                detail += f"\n{file_path}"
            color = COLORS["success"] if status.get("success") else COLORS["danger"]
            self.status_label.setText(detail)
            self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")
        else:
            self.status_label.setText("Aucune sauvegarde n’a encore été exécutée.")
            self.status_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 13px;")

    def _choose_folder(self):
        initial = self.folder_edit.text().strip() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sauvegarde", initial)
        if selected:
            self.folder_edit.setText(os.path.normpath(selected))

    def _save_schedule(self):
        settings = self._settings_from_form()
        try:
            if settings.enabled:
                register_scheduled_task(settings)
            else:
                delete_scheduled_task()
            save_settings(settings)
        except BackupError as exc:
            QMessageBox.critical(self, "Planification impossible", str(exc))
            return
        QMessageBox.information(
            self,
            "Planification enregistrée",
            "La sauvegarde quotidienne est activée."
            if settings.enabled
            else "La sauvegarde automatique est désactivée.",
        )

    def _backup_now(self):
        settings = self._settings_from_form()
        try:
            validate_settings(settings, require_directory=True)
        except BackupError as exc:
            QMessageBox.warning(self, "Configuration incomplète", str(exc))
            return

        self._set_busy(True)
        self.status_label.setText("Sauvegarde en cours…")
        self.status_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px;")
        self._worker = _BackupWorker(settings, self)
        self._worker.succeeded.connect(self._backup_succeeded)
        self._worker.failed.connect(self._backup_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _backup_succeeded(self, result):
        self.refresh_data()
        QMessageBox.information(
            self,
            "Sauvegarde terminée",
            f"La base a été sauvegardée avec succès :\n\n{result.file_path}",
        )

    def _backup_failed(self, message: str):
        self.refresh_data()
        QMessageBox.critical(self, "Échec de la sauvegarde", message)

    def _set_busy(self, busy: bool):
        self.backup_button.setEnabled(not busy)
        self.save_button.setEnabled(not busy)
        self.backup_button.setText("Sauvegarde en cours…" if busy else "Sauvegarder maintenant")

    def _open_folder(self):
        folder = self.folder_edit.text().strip()
        if not folder or not Path(folder).exists():
            QMessageBox.warning(self, "Dossier introuvable", "Choisissez d’abord un dossier existant.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
