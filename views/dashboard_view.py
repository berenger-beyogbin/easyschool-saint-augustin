from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView,
)
from PySide6.QtCore import Qt

from app.config import Config
from app.session import AppSession
from app.styles import (
    COLORS, BUTTON_PRIMARY, apply_card_shadow
)
from services.dashboard_service import DashboardService
from views.ui_components import KpiCard, make_separator


class DashboardView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._init_layout()
        self.refresh_data()

    # -------------------------------------------------------------------------
    # CONSTRUCTION
    # -------------------------------------------------------------------------

    def _init_layout(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg']}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(24, 20, 24, 24)
        self.main_layout.setSpacing(20)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._build_cartes()
        self._build_tables()
        self.main_layout.addStretch()

    def _build_header(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        apply_card_shadow(frame)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(0)

        # --- Colonne gauche ---
        left = QVBoxLayout()
        left.setSpacing(5)

        lbl_title = QLabel("Tableau de bord")
        lbl_title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {COLORS['text']};"
            "background-color: transparent; border: none; letter-spacing: -0.2px;"
        )
        left.addWidget(lbl_title)

        self.lbl_annee_active = QLabel("Année scolaire : chargement…")
        self.lbl_annee_active.setStyleSheet(
            "font-size: 12px; color: #64748B; background-color: transparent; border: none;"
        )
        left.addWidget(self.lbl_annee_active)

        self.lbl_etab = QLabel("")
        self.lbl_etab.setStyleSheet(
            "font-size: 11px; color: #94A3B8; background-color: transparent; border: none;"
        )
        left.addWidget(self.lbl_etab)

        layout.addLayout(left)
        layout.addStretch()

        # --- Colonne droite ---
        right = QVBoxLayout()
        right.setSpacing(7)
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)

        lbl_date = QLabel(f"📅  {date.today().strftime('%A %d %B %Y').capitalize()}")
        lbl_date.setStyleSheet(
            "font-size: 12px; color: #64748B; background-color: transparent; border: none;"
        )
        lbl_date.setAlignment(Qt.AlignRight)
        right.addWidget(lbl_date)

        try:
            username = AppSession.get_logged_in_username()
        except Exception:
            username = "—"
        self.lbl_user = QLabel(f"●  {username}")
        self.lbl_user.setStyleSheet(
            "font-size: 12px; color: #64748B; background-color: transparent; border: none;"
        )
        self.lbl_user.setAlignment(Qt.AlignRight)
        right.addWidget(self.lbl_user)

        btn_refresh = QPushButton("↺  Actualiser")
        btn_refresh.setStyleSheet(BUTTON_PRIMARY)
        btn_refresh.setFixedWidth(130)
        btn_refresh.setFixedHeight(34)
        btn_refresh.clicked.connect(self.refresh_data)
        right.addWidget(btn_refresh)

        layout.addLayout(right)
        self.main_layout.addWidget(frame)

    def _build_cartes(self):
        self.kpi_cards = {}

        show_scolarite    = AppSession.has_permission("SCOLARITE_VIEW")
        show_versements   = AppSession.has_permission("SCOLARITE_VERSEMENTS")
        show_kiosque      = AppSession.has_permission("KIOSQUE_VIEW")
        show_comptabilite = AppSession.has_permission("COMPTABILITE_VIEW")

        # (visible_ligne, cartes)
        grid_defs = [
            (show_scolarite, [
                ("total_inscrits",             "Élèves inscrits",        COLORS["primary"],  "🎓"),
                ("total_nouveaux",             "Nouveaux élèves",        COLORS["success"],  "✨"),
                ("total_classes",              "Classes actives",        "#0369A1",          "🏫"),
            ]),
            (show_versements, [
                ("total_versements_scolarite", "Versements scolarité",   COLORS["success"],  "💳"),
                ("total_versements_cantine",   "Versements cantine",     COLORS["warning"],  "🍽"),
                ("total_versements_transport", "Versements transport",   COLORS["warning"],  "🚌"),
            ]),
            (show_kiosque or show_comptabilite, [
                ("total_ventes_kiosque",       "Ventes kiosque",         COLORS["primary"],  "🛒"),
                ("total_depenses",             "Dépenses compta",        COLORS["danger"],   "📤"),
                ("total_recettes",             "Recettes compta",        COLORS["success"],  "📥"),
            ]),
        ]

        for row_visible, row_defs in grid_defs:
            row_widget = QWidget()
            row_widget.setStyleSheet("background-color: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(14)
            for key, title, color, icon in row_defs:
                card = KpiCard(title=title, color=color, icon=icon)
                self.kpi_cards[key] = card
                row_layout.addWidget(card)
            row_widget.setVisible(row_visible)
            self.main_layout.addWidget(row_widget)

        # Visibilité par carte individuelle pour la ligne mixte kiosque / compta
        self.kpi_cards["total_ventes_kiosque"].setVisible(show_kiosque)
        self.kpi_cards["total_depenses"].setVisible(show_comptabilite)
        self.kpi_cards["total_recettes"].setVisible(show_comptabilite)

        # Cantine / Transport désactivés pour la version collège CJGA
        self.kpi_cards["total_versements_cantine"].setVisible(show_versements and Config.ENABLE_CANTINE)
        self.kpi_cards["total_versements_transport"].setVisible(show_versements and Config.ENABLE_TRANSPORT)

    def _build_alertes(self):
        self.alertes_frame = QFrame()
        self.alertes_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        apply_card_shadow(self.alertes_frame)
        frame_layout = QVBoxLayout(self.alertes_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Titre section
        header_row = QHBoxLayout()
        header_row.setContentsMargins(18, 16, 18, 12)
        header_row.setSpacing(10)

        lbl_icon = QLabel("🔔")
        lbl_icon.setStyleSheet("font-size: 14px; background-color: transparent; border: none;")
        header_row.addWidget(lbl_icon)

        lbl_title = QLabel("Alertes")
        lbl_title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {COLORS['text']};"
            "background-color: transparent; border: none;"
        )
        header_row.addWidget(lbl_title, 1)

        self.lbl_alerte_count = QLabel("")
        self.lbl_alerte_count.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #DC2626; background-color: #FEF2F2;"
            "border-radius: 10px; padding: 1px 8px; border: none;"
        )
        header_row.addWidget(self.lbl_alerte_count)

        frame_layout.addLayout(header_row)

        sep = make_separator()
        frame_layout.addWidget(sep)

        self.alertes_content = QWidget()
        self.alertes_content.setStyleSheet("background-color: transparent;")
        self.alertes_layout = QVBoxLayout(self.alertes_content)
        self.alertes_layout.setContentsMargins(18, 12, 18, 16)
        self.alertes_layout.setSpacing(4)

        lbl_init = QLabel("Chargement des alertes…")
        lbl_init.setStyleSheet("color: #94A3B8; font-size: 12px; background-color: transparent; border: none;")
        self.alertes_layout.addWidget(lbl_init)

        frame_layout.addWidget(self.alertes_content)
        self.main_layout.addWidget(self.alertes_frame)

    def _build_tables(self):
        show_versements = AppSession.has_permission("SCOLARITE_VERSEMENTS")
        show_ventes     = AppSession.has_permission("KIOSQUE_VIEW")

        tables_widget = QWidget()
        tables_widget.setStyleSheet("background-color: transparent;")
        outer = QHBoxLayout(tables_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)

        tables_def = [
            ("tbl_versements", "Derniers versements", ["Date", "Matricule", "Élève", "Scolarité", "Cantine", "Transport"], 2, show_versements),
            ("tbl_ventes",     "Dernières ventes",    ["Date", "Article", "Qté", "Montant"],                               1, show_ventes),
        ]

        for attr, title, headers, stretch, visible in tables_def:
            panel = QFrame()
            panel.setVisible(visible)
            panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
            apply_card_shadow(panel)
            p_layout = QVBoxLayout(panel)
            p_layout.setContentsMargins(0, 0, 0, 0)
            p_layout.setSpacing(0)

            # Header panneau
            h_row = QHBoxLayout()
            h_row.setContentsMargins(16, 14, 16, 10)
            lbl = QLabel(title.upper())
            lbl.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 0.6px;"
                "background-color: transparent; border: none;"
            )
            h_row.addWidget(lbl)
            p_layout.addLayout(h_row)

            sep = make_separator()
            p_layout.addWidget(sep)

            tbl = self._create_table(headers)
            p_layout.addWidget(tbl)
            setattr(self, attr, tbl)
            outer.addWidget(panel, stretch)

        self.tbl_versements.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_ventes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Cantine / Transport désactivés pour la version collège CJGA
        if not Config.ENABLE_CANTINE:
            self.tbl_versements.setColumnHidden(4, True)
        if not Config.ENABLE_TRANSPORT:
            self.tbl_versements.setColumnHidden(5, True)
        tables_widget.setVisible(show_versements or show_ventes)
        self.main_layout.addWidget(tables_widget)

    def _create_table(self, headers: list) -> QTableWidget:
        tbl = QTableWidget()
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setRowCount(0)
        tbl.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                border-radius: 0 0 12px 12px;
                background-color: {COLORS['card']};
                color: {COLORS['text']};
                font-size: 12px;
                alternate-background-color: {COLORS['table_row_alt']};
                selection-background-color: {COLORS['table_selected']};
                selection-color: {COLORS['text']};
                outline: none;
                gridline-color: {COLORS['border_soft']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['table_selected']};
                color: {COLORS['text']};
            }}
            QHeaderView::section {{
                background-color: #F1F5F9;
                padding: 8px 10px;
                font-weight: 700;
                font-size: 11px;
                color: #475569;
                border: none;
                border-right: 1px solid {COLORS['border_soft']};
                border-bottom: 1px solid {COLORS['border']};
                letter-spacing: 0.3px;
            }}
            QHeaderView::section:last {{ border-right: none; }}
        """)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setHighlightSections(False)
        tbl.setMaximumHeight(190)
        tbl.setFrameShape(QFrame.NoFrame)
        return tbl

    # -------------------------------------------------------------------------
    # DATA REFRESH
    # -------------------------------------------------------------------------

    def refresh_data(self):
        try:
            summary = DashboardService.get_dashboard_summary()

            if AppSession.has_permission("SCOLARITE_VIEW"):
                self.kpi_cards["total_inscrits"].set_value(str(summary["total_inscrits"]))
                self.kpi_cards["total_nouveaux"].set_value(str(summary["total_nouveaux"]))
                self.kpi_cards["total_classes"].set_value(str(summary["total_classes"]))

            if AppSession.has_permission("SCOLARITE_VERSEMENTS"):
                self.kpi_cards["total_versements_scolarite"].set_value(
                    DashboardService.format_fcfa(summary["total_versements_scolarite"]))
                self.kpi_cards["total_versements_cantine"].set_value(
                    DashboardService.format_fcfa(summary["total_versements_cantine"]))
                self.kpi_cards["total_versements_transport"].set_value(
                    DashboardService.format_fcfa(summary["total_versements_transport"]))
                self._update_table(
                    self.tbl_versements,
                    DashboardService.get_latest_versements(),
                    right_align_cols=[3, 4, 5],
                )

            if AppSession.has_permission("KIOSQUE_VIEW"):
                self.kpi_cards["total_ventes_kiosque"].set_value(
                    DashboardService.format_fcfa(summary["total_ventes_kiosque"]))
                self._update_table(
                    self.tbl_ventes,
                    DashboardService.get_latest_ventes(),
                    right_align_cols=[2, 3],
                )

            if AppSession.has_permission("COMPTABILITE_VIEW"):
                self.kpi_cards["total_depenses"].set_value(
                    DashboardService.format_fcfa(summary["total_depenses"]))
                self.kpi_cards["total_recettes"].set_value(
                    DashboardService.format_fcfa(summary["total_recettes"]))

        except Exception as e:
            print(f"Erreur refresh_data DashboardView : {e}")

    def _update_alertes(self):
        self._clear_layout(self.alertes_layout)
        has_alerts = False
        count = 0

        stock_alerts = DashboardService.get_stock_alerts()
        if stock_alerts:
            has_alerts = True
            count += len(stock_alerts)
            lbl = QLabel(f"⚠  Stock faible — {len(stock_alerts)} article(s) sous le seuil d'alerte")
            lbl.setStyleSheet(
                "color: #D97706; font-size: 12px; font-weight: 700;"
                "background-color: transparent; border: none; padding: 4px 0 2px 0;"
            )
            self.alertes_layout.addWidget(lbl)
            for a in stock_alerts[:4]:
                detail = QLabel(f"  • {a['article']}  —  stock : {a['stock']}  /  seuil : {a['seuil']}")
                detail.setStyleSheet(
                    "color: #64748B; font-size: 11px; background-color: transparent;"
                    "border: none; padding: 1px 0 1px 10px;"
                )
                self.alertes_layout.addWidget(detail)

        cap_alerts = DashboardService.get_classes_capacity_alerts()
        if cap_alerts:
            has_alerts = True
            count += len(cap_alerts)
            lbl = QLabel(f"⚠  Capacité — {len(cap_alerts)} classe(s) à 90 % ou plus de leur capacité")
            lbl.setStyleSheet(
                "color: #D97706; font-size: 12px; font-weight: 700;"
                "background-color: transparent; border: none; padding: 4px 0 2px 0;"
            )
            self.alertes_layout.addWidget(lbl)
            for a in cap_alerts[:4]:
                detail = QLabel(f"  • {a['classe']}  —  {a['effectif']} / {a['capacite']} élèves ({a['pct']} %)")
                detail.setStyleSheet(
                    "color: #64748B; font-size: 11px; background-color: transparent;"
                    "border: none; padding: 1px 0 1px 10px;"
                )
                self.alertes_layout.addWidget(detail)

        impayes = DashboardService.get_impayes_scolarite()
        if impayes:
            has_alerts = True
            count += len(impayes)
            lbl = QLabel(f"⛔  Impayés scolarité — {len(impayes)} élève(s) avec un reste à payer")
            lbl.setStyleSheet(
                "color: #DC2626; font-size: 12px; font-weight: 700;"
                "background-color: transparent; border: none; padding: 4px 0 2px 0;"
            )
            self.alertes_layout.addWidget(lbl)
            for a in impayes[:4]:
                detail = QLabel(
                    f"  • {a['eleve']} ({a['classe']})  —  dû : {a['du']}  ·  versé : {a['verse']}  ·  reste : {a['reste']}"
                )
                detail.setStyleSheet(
                    "color: #64748B; font-size: 11px; background-color: transparent;"
                    "border: none; padding: 1px 0 1px 10px;"
                )
                self.alertes_layout.addWidget(detail)

        if not has_alerts:
            ok_row = QHBoxLayout()
            lbl_ok = QLabel("✓  Aucune alerte — tout est en ordre.")
            lbl_ok.setStyleSheet(
                "color: #16A34A; font-size: 12px; font-weight: 600;"
                "background-color: transparent; border: none; padding: 4px 0;"
            )
            ok_row.addWidget(lbl_ok)
            ok_row.addStretch()
            self.alertes_layout.addLayout(ok_row)
            self.lbl_alerte_count.setText("")
        else:
            self.lbl_alerte_count.setText(f"{count} alerte(s)")

    def _update_table(self, table: QTableWidget, data: list, right_align_cols: list = None):
        right_align_cols = right_align_cols or []
        table.setRowCount(0)

        if not data:
            table.setRowCount(1)
            item0 = QTableWidgetItem("Aucune donnée disponible")
            item0.setForeground(Qt.gray)
            item0.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(0, 0, item0)
            for col in range(1, table.columnCount()):
                table.setItem(0, col, QTableWidgetItem(""))
            return

        table.setRowCount(len(data))
        keys = list(data[0].keys())
        for row_idx, row_data in enumerate(data):
            table.setRowHeight(row_idx, 34)
            for col_idx, key in enumerate(keys):
                val = str(row_data.get(key, ""))
                item = QTableWidgetItem(val)
                if col_idx in right_align_cols:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row_idx, col_idx, item)

        table.resizeColumnsToContents()

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_layout(sub)

    def _goto_module(self, menu_index: int):
        if self.main_window and hasattr(self.main_window, "menu_list"):
            self.main_window.menu_list.setCurrentRow(menu_index)
