from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from services.etablissement_service import EtablissementService
from app.styles import COLORS, PAGE_TITLE_STYLE, INPUT_STYLE, BUTTON_PRIMARY, BUTTON_SECONDARY

class EtablissementView(QWidget):
    """
    Ecran : FICHE D'IDENTIFICATION DE L'ETABLISSEMENT
    Visualisation et modification des informations de l'ecole.
    """
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        # Layout principal vertical
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Titre de la fiche
        titre = QLabel("Fiche d'Identification de l'Établissement")
        titre.setStyleSheet(PAGE_TITLE_STYLE)
        self.layout.addWidget(titre)

        # Formulaire en grille
        form_grid = QGridLayout()
        form_grid.setSpacing(10)

        # Creation des champs de saisie (Inputs)
        self.txt_nom = QLineEdit()
        self.txt_sigle = QLineEdit()
        self.txt_tel = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_adresse = QLineEdit()
        self.txt_chef = QLineEdit()
        self.txt_slogan = QLineEdit()
        self.txt_localite = QLineEdit()
        self.txt_code = QLineEdit()
        self.txt_type_ens = QLineEdit()
        self.txt_ministere = QLineEdit()
        self.txt_dren = QLineEdit()
        self.txt_iepp = QLineEdit()

        # Ajout des labels et champs dans la grille (Ligne, Colonne)
        labels_champs = [
            ("Nom Etab. * :", self.txt_nom, 0, 0),
            ("Sigle :", self.txt_sigle, 0, 2),
            ("Téléphone :", self.txt_tel, 1, 0),
            ("E-Mail :", self.txt_email, 1, 2),
            ("Adresse :", self.txt_adresse, 2, 0),
            ("Chef d'Etab. :", self.txt_chef, 2, 2),
            ("Slogan :", self.txt_slogan, 3, 0),
            ("Localité :", self.txt_localite, 3, 2),
            ("Code Etab. :", self.txt_code, 4, 0),
            ("Type Enseignement :", self.txt_type_ens, 4, 2),
            ("Ministère :", self.txt_ministere, 5, 0),
            ("DREN :", self.txt_dren, 5, 2),
            ("IEP / IEPP :", self.txt_iepp, 6, 0)
        ]

        for text, widget, row, col in labels_champs:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-weight: 500; color: {COLORS['text_soft']}; background-color: transparent;")
            form_grid.addWidget(lbl, row, col)
            form_grid.addWidget(widget, row, col + 1)
            widget.setStyleSheet(INPUT_STYLE)

        self.layout.addLayout(form_grid)

        # Zone de Logo (Visualisation + Parcourir)
        logo_layout = QHBoxLayout()
        self.lbl_logo_path = QLabel("Aucun fichier selectionne")
        self.lbl_logo_path.setStyleSheet(f"color: {COLORS['muted']}; font-style: italic; background-color: transparent;")
        btn_parcourir = QPushButton("Parcourir...")
        btn_parcourir.setStyleSheet(BUTTON_SECONDARY)
        btn_parcourir.clicked.connect(self.parcourir_logo)
        
        logo_layout.addWidget(QLabel("Logo de l'école :"))
        logo_layout.addWidget(self.lbl_logo_path)
        logo_layout.addWidget(btn_parcourir)
        logo_layout.addStretch()
        self.layout.addLayout(logo_layout)

        # Boutons d'Action en bas
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()

        self.btn_valider = QPushButton("Valider")
        self.btn_valider.setStyleSheet(BUTTON_PRIMARY)
        self.btn_valider.clicked.connect(self.valider_formulaire)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(BUTTON_SECONDARY)
        btn_fermer.clicked.connect(self.close_tab)

        actions_layout.addWidget(self.btn_valider)
        actions_layout.addWidget(btn_fermer)
        self.layout.addLayout(actions_layout)

        # Petit message d'aide pour debutante
        lbl_aide = QLabel("* Les champs avec asterisques sont obligatoires.")
        lbl_aide.setStyleSheet("font-size: 11px; color: #9ca3af; font-style: italic;")
        self.layout.addWidget(lbl_aide)

    def load_data(self):
        """Charge les informations existantes de l'etablissement."""
        try:
            ecole = EtablissementService.get_etablissement()
            if ecole:
                self.txt_nom.setText(ecole.RaisonSociale)
                self.txt_sigle.setText(ecole.Sigle or "")
                self.txt_tel.setText(ecole.Telephone or "")
                self.txt_email.setText(ecole.Email or "")
                self.txt_adresse.setText(ecole.Adresse or "")
                self.txt_chef.setText(ecole.ChefEtab or "")
                self.txt_slogan.setText(ecole.Slogan or "")
                self.txt_localite.setText(ecole.Localite or "")
                self.txt_code.setText(ecole.CodeEtab or "")
                self.txt_type_ens.setText(ecole.TypeEtab or "")
                self.txt_ministere.setText(ecole.Ministere or "")
                self.txt_dren.setText(ecole.Dren or "")
                self.txt_iepp.setText(ecole.IEP or "")
                self.lbl_logo_path.setText(ecole.LogoPath or "Aucun fichier selectionne")
        except Exception as e:
            QMessageBox.critical(self, "Erreur base de données", f"Impossible de charger les données : {e}")

    def parcourir_logo(self):
        """Ouvre une boite de dialogue pour choisir une image de logo."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Choisir le logo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            import os
            import shutil
            try:
                base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                logos_dir = os.path.join(base_dir, "assets", "logos")
                os.makedirs(logos_dir, exist_ok=True)
                
                filename = os.path.basename(file_path)
                dest_path = os.path.join(logos_dir, filename)
                shutil.copy2(file_path, dest_path)
                
                rel_path = f"assets/logos/{filename}"
                self.lbl_logo_path.setText(rel_path)
            except Exception as e:
                QMessageBox.warning(self, "Erreur de copie", f"Impossible de copier le logo : {e}")

    def valider_formulaire(self):
        """Valide et enregistre la fiche."""
        # Verification des champs obligatoires
        nom = self.txt_nom.text().strip()
        if not nom:
            QMessageBox.warning(self, "Champ obligatoire", "Le nom de l'établissement est requis !")
            return

        # Compilation des donnees
        data = {
            "RaisonSociale": nom,
            "Sigle": self.txt_sigle.text().strip(),
            "Telephone": self.txt_tel.text().strip(),
            "Email": self.txt_email.text().strip(),
            "Adresse": self.txt_adresse.text().strip(),
            "ChefEtab": self.txt_chef.text().strip(),
            "Slogan": self.txt_slogan.text().strip(),
            "Localite": self.txt_localite.text().strip(),
            "CodeEtab": self.txt_code.text().strip(),
            "TypeEtab": self.txt_type_ens.text().strip(),
            "Ministere": self.txt_ministere.text().strip(),
            "Dren": self.txt_dren.text().strip(),
            "IEP": self.txt_iepp.text().strip(),
            "LogoPath": self.lbl_logo_path.text() if self.lbl_logo_path.text() != "Aucun fichier selectionne" else None
        }

        # Enregistrement via le service
        reussite = EtablissementService.save_etablissement(data)
        if reussite:
            QMessageBox.information(self, "Enregistrement réussi", "La fiche d'identification de l'établissement a été mise à jour.")
        else:
            QMessageBox.critical(self, "Erreur", "Une erreur est survenue lors de l'enregistrement.")

    def close_tab(self):
        # Pour EtablissementView, le bouton Fermer peut simplement recharger les anciennes données depuis la base.
        self.load_data()
        QMessageBox.information(self, "Réinitialisation", "Le formulaire a été réinitialisé avec les données enregistrées.")
