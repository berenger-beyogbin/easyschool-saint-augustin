from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QListView, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.session import AppSession
from app.styles import BUTTON_PRIMARY, COLORS, apply_card_shadow
from services.dashboard_service import DashboardService
from services.dashboard_v2_service import DashboardV2Service


def _money(value) -> str:
    return DashboardService.format_fcfa(value)


class CardIcon(QWidget):
    """Pictogramme vectoriel homogène, net quelle que soit la résolution."""

    def __init__(self, name: str, color: str, size: int = 34, parent=None):
        super().__init__(parent)
        self.name = name
        self.color = QColor(color)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def sizeHint(self):
        return QSize(self._size, self._size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Le fond teinté donne plus de présence à l'icône sans alourdir la carte.
        background = QColor(self.color)
        background.setAlpha(22)
        painter.setPen(Qt.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 9, 9)

        painter.translate(self.width() / 2, self.height() / 2)
        scale = self._size / 34.0
        painter.scale(scale, scale)
        pen = QPen(self.color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        self._draw(painter)

    @staticmethod
    def _line(painter, x1, y1, x2, y2):
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw(self, painter):
        if self.name == "school":
            roof = QPainterPath()
            roof.moveTo(-9, -4); roof.lineTo(0, -10); roof.lineTo(9, -4)
            painter.drawPath(roof)
            painter.drawRect(QRectF(-7.5, -3, 15, 11))
            painter.drawRect(QRectF(-2, 2, 4, 6))
            self._line(painter, -4.8, 0, -4.8, 2.5)
            self._line(painter, 4.8, 0, 4.8, 2.5)
        elif self.name == "canteen":
            # Assiette, fourchette et couteau.
            painter.drawEllipse(QRectF(-5.5, -5.5, 11, 11))
            painter.drawEllipse(QRectF(-2.5, -2.5, 5, 5))
            self._line(painter, -8.5, -7, -8.5, 8)
            for x in (-10, -8.5, -7):
                self._line(painter, x, -7, x, -3)
            self._line(painter, 8.5, -7, 8.5, 8)
            self._line(painter, 6.5, -7, 6.5, -1)
            self._line(painter, 6.5, -1, 8.5, -1)
        elif self.name == "bus":
            painter.drawRoundedRect(QRectF(-9, -8, 18, 14), 3, 3)
            painter.drawRect(QRectF(-6.5, -5.5, 13, 5))
            painter.drawEllipse(QRectF(-6.5, 4, 4, 4))
            painter.drawEllipse(QRectF(2.5, 4, 4, 4))
            self._line(painter, -6, 2, -3.5, 2)
            self._line(painter, 3.5, 2, 6, 2)
        elif self.name == "students":
            painter.drawEllipse(QRectF(-3.5, -8, 7, 7))
            painter.drawArc(QRectF(-8, -1, 16, 11), 0, 180 * 16)
            painter.drawEllipse(QRectF(5, -5, 4.5, 4.5))
            painter.drawArc(QRectF(4, 0, 8, 7), 0, 180 * 16)
        elif self.name == "income":
            painter.drawRoundedRect(QRectF(-9, -6, 18, 13), 3, 3)
            painter.drawRoundedRect(QRectF(2, -2, 8, 6), 2, 2)
            painter.drawEllipse(QRectF(4.8, -0.2, 2, 2))
            self._line(painter, -5, -9, 5, -9)
        elif self.name == "expense":
            painter.drawRoundedRect(QRectF(-9, -6, 18, 13), 3, 3)
            self._line(painter, -4, -9, 6, -9)
            self._line(painter, 2, -2, 9, -9)
            self._line(painter, 4.5, -9, 9, -9)
            self._line(painter, 9, -9, 9, -4.5)
        elif self.name == "balance":
            self._line(painter, 0, -9, 0, 8)
            self._line(painter, -8, -6, 8, -6)
            self._line(painter, -6, -6, -9, 2)
            self._line(painter, 6, -6, 9, 2)
            painter.drawArc(QRectF(-12, -2, 6, 7), 180 * 16, 180 * 16)
            painter.drawArc(QRectF(6, -2, 6, 7), 180 * 16, 180 * 16)
            self._line(painter, -5, 8, 5, 8)
        elif self.name == "cart":
            self._line(painter, -10, -8, -7, -8)
            self._line(painter, -7, -8, -4.5, 3)
            basket = QPainterPath()
            basket.moveTo(-5.5, -4); basket.lineTo(9, -4)
            basket.lineTo(6.5, 3); basket.lineTo(-4.5, 3)
            painter.drawPath(basket)
            painter.drawEllipse(QRectF(-4, 5, 3, 3))
            painter.drawEllipse(QRectF(4.5, 5, 3, 3))
        elif self.name == "stock":
            box = QPainterPath()
            box.moveTo(0, -9); box.lineTo(9, -4); box.lineTo(9, 5)
            box.lineTo(0, 10); box.lineTo(-9, 5); box.lineTo(-9, -4)
            box.closeSubpath()
            painter.drawPath(box)
            self._line(painter, -9, -4, 0, 1)
            self._line(painter, 9, -4, 0, 1)
            self._line(painter, 0, 1, 0, 10)
            self._line(painter, -4.5, -6.5, 4.5, -1.5)
        elif self.name == "receipt":
            receipt = QPainterPath()
            receipt.moveTo(-7, -9); receipt.lineTo(7, -9); receipt.lineTo(7, 9)
            receipt.lineTo(4, 7); receipt.lineTo(1, 9); receipt.lineTo(-2, 7)
            receipt.lineTo(-5, 9); receipt.lineTo(-7, 7); receipt.closeSubpath()
            painter.drawPath(receipt)
            self._line(painter, -3.5, -4, 3.5, -4)
            self._line(painter, -3.5, 0, 3.5, 0)
            self._line(painter, -3.5, 4, 1.5, 4)
        elif self.name == "discount":
            painter.drawEllipse(QRectF(-7.5, -8, 4.5, 4.5))
            painter.drawEllipse(QRectF(3, 3.5, 4.5, 4.5))
            self._line(painter, -7, 8, 7, -8)


class RecoveryCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, color: str, icon: str):
        super().__init__()
        self.color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame {{ background: {COLORS['card']}; border: 1px solid {COLORS['border']}; border-radius: 12px; }}
            QFrame:hover {{ border-color: {color}; }}
            QLabel {{ background: transparent; border: none; }}
        """)
        apply_card_shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 14, 17, 13)
        layout.setSpacing(6)
        top = QHBoxLayout()
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size:13px;font-weight:700;color:#475569;")
        top.addWidget(self.title)
        top.addStretch()
        top.addWidget(CardIcon(icon, color, size=36))
        layout.addLayout(top)
        self.value = QLabel("—")
        self.value.setStyleSheet("font-size:23px;font-weight:800;color:#0F172A;")
        layout.addWidget(self.value)
        self.detail = QLabel("")
        self.detail.setStyleSheet("font-size:11px;color:#64748B;")
        layout.addWidget(self.detail)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(7)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar{{border:none;background:#E2E8F0;border-radius:3px;}} QProgressBar::chunk{{background:{color};border-radius:3px;}}")
        layout.addWidget(self.progress)
        self.rate = QLabel("")
        self.rate.setAlignment(Qt.AlignRight)
        self.rate.setStyleSheet(f"font-size:11px;font-weight:700;color:{color};")
        layout.addWidget(self.rate)

    def set_data(self, data: dict):
        if data["due"] <= 0:
            self.value.setText("Aucun frais configuré")
            self.value.setStyleSheet("font-size:18px;font-weight:750;color:#475569;")
            self.detail.setText("Aucun montant attendu pour cette année")
            self.progress.hide()
            self.rate.setText("Non applicable")
            self.rate.setStyleSheet("font-size:11px;font-weight:650;color:#64748B;")
            return

        self.value.setStyleSheet("font-size:23px;font-weight:800;color:#0F172A;")
        self.value.setText(_money(data["paid"]))
        self.detail.setText(f"Encaissé sur {_money(data['due'])}  ·  Reste {_money(data['remaining'])}")
        self.progress.show()
        self.progress.setValue(data["rate"])
        self.rate.setText(f"Taux de recouvrement : {data['rate']} %")
        self.rate.setStyleSheet(f"font-size:11px;font-weight:700;color:{self.color};")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, color: str, icon: str, compact: bool = False):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(90 if compact else 110)
        self.setStyleSheet(f"QFrame{{background:white;border:1px solid {COLORS['border']};border-radius:12px;}} QFrame:hover{{border-color:{color};}} QLabel{{background:transparent;border:none;}}")
        apply_card_shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        top = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-size:12px;font-weight:650;color:#64748B;")
        top.addWidget(label)
        top.addStretch()
        top.addWidget(CardIcon(icon, color, size=34))
        layout.addLayout(top)
        self.value = QLabel("—")
        self.value.setStyleSheet("font-size:22px;font-weight:800;color:#0F172A;")
        layout.addWidget(self.value)
        self.note = QLabel("")
        self.note.setStyleSheet("font-size:10px;color:#94A3B8;")
        layout.addWidget(self.note)

    def set_data(self, value: str, note: str = ""):
        self.value.setText(value)
        self.note.setText(note)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DashboardV2View(QWidget):
    PERIODS = {
        "Aujourd’hui": "today",
        "Ce mois": "month",
        "Année scolaire": "year",
    }

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._build()
        self.refresh_data()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        body.setStyleSheet(f"background:{COLORS['bg']};")
        self.layout = QVBoxLayout(body)
        self.layout.setContentsMargins(22, 18, 22, 24)
        self.layout.setSpacing(16)
        scroll.setWidget(body)
        root.addWidget(scroll)

        self._build_header()
        self._build_recovery()
        self._build_metrics()
        self._build_activity()
        self.layout.addStretch()

    def _build_header(self):
        panel = QFrame()
        panel.setStyleSheet(f"QFrame{{background:white;border:1px solid {COLORS['border']};border-radius:12px;}} QLabel{{background:transparent;border:none;}}")
        row = QHBoxLayout(panel)
        row.setContentsMargins(18, 13, 18, 13)
        text = QVBoxLayout()
        title = QLabel("Tableau de bord de pilotage")
        title.setStyleSheet("font-size:20px;font-weight:800;color:#0F172A;")
        text.addWidget(title)
        self.subtitle = QLabel("")
        self.subtitle.setStyleSheet("font-size:11px;color:#64748B;")
        text.addWidget(self.subtitle)
        row.addLayout(text)
        row.addStretch()
        self.period = QComboBox()
        self.period.addItems(self.PERIODS.keys())
        self.period.setCurrentText("Année scolaire")
        self.period.setMinimumWidth(155)
        self.period.setFixedHeight(34)
        period_view = QListView(self.period)
        period_view.setMouseTracking(True)
        period_view.setStyleSheet("""
            QListView {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                outline: none;
                padding: 3px;
            }
            QListView::item {
                min-height: 30px;
                padding: 3px 8px;
                color: #0F172A;
                background-color: #FFFFFF;
            }
            QListView::item:hover {
                color: #1E3A8A;
                background-color: #DBEAFE;
            }
            QListView::item:selected,
            QListView::item:selected:hover {
                color: #FFFFFF;
                background-color: #2563EB;
            }
        """)
        period_palette = period_view.palette()
        period_palette.setColor(QPalette.Highlight, QColor("#2563EB"))
        period_palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        period_palette.setColor(QPalette.Text, QColor("#0F172A"))
        period_palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        period_view.setPalette(period_palette)
        self.period.setView(period_view)
        self.period.setStyleSheet(f"""
            QComboBox {{
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid {COLORS['border']};
                border-radius: 7px;
                padding: 5px 30px 5px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary']};
                color: #0F172A;
            }}
            QComboBox:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        self.period.currentTextChanged.connect(self.refresh_data)
        row.addWidget(self.period)
        refresh = QPushButton("Actualiser")
        refresh.setStyleSheet(BUTTON_PRIMARY)
        refresh.clicked.connect(self.refresh_data)
        row.addWidget(refresh)
        self.layout.addWidget(panel)

    def _build_recovery(self):
        title = QLabel("RECOUVREMENT DES FRAIS · ANNÉE SCOLAIRE")
        title.setStyleSheet("font-size:11px;font-weight:800;color:#64748B;letter-spacing:1px;")
        self.layout.addWidget(title)
        row = QHBoxLayout()
        row.setSpacing(12)
        self.recovery_cards = {
            "scolarite": RecoveryCard("Scolarité", "#2563EB", "school"),
            "cantine": RecoveryCard("Cantine", "#16A34A", "canteen"),
            "transport": RecoveryCard("Transport", "#D97706", "bus"),
        }
        for card in self.recovery_cards.values():
            card.clicked.connect(lambda: self._goto_module(4))
            row.addWidget(card)
        self.layout.addLayout(row)

    def _build_metrics(self):
        self.activity_title = QLabel("INDICATEURS CLÉS · ANNÉE SCOLAIRE")
        self.activity_title.setStyleSheet("font-size:11px;font-weight:800;color:#64748B;letter-spacing:1px;")
        self.layout.addWidget(self.activity_title)

        primary_grid = QGridLayout()
        primary_grid.setHorizontalSpacing(12)
        primary_specs = [
            ("inscrits", "Élèves inscrits", "#2563EB", "students"),
            ("recettes", "Encaissements", "#059669", "income"),
            ("depenses", "Dépenses", "#DC2626", "expense"),
            ("solde", "Solde net", "#16A34A", "balance"),
        ]
        self.metrics = {}
        for i, (key, label, color, icon) in enumerate(primary_specs):
            card = MetricCard(label, color, icon)
            self.metrics[key] = card
            primary_grid.addWidget(card, 0, i)
        self.layout.addLayout(primary_grid)

        secondary_title = QLabel("ACTIVITÉ COMPLÉMENTAIRE")
        secondary_title.setStyleSheet("font-size:11px;font-weight:800;color:#64748B;letter-spacing:1px;")
        self.layout.addWidget(secondary_title)
        secondary_grid = QGridLayout()
        secondary_grid.setHorizontalSpacing(12)
        secondary_specs = [
            ("kiosque", "Ventes kiosque", "#7C3AED", "cart"),
            ("stock", "Valeur du stock", "#0369A1", "stock"),
            ("autres", "Autres frais", "#0F766E", "receipt"),
            ("reductions", "Réductions", "#D97706", "discount"),
        ]
        for i, (key, label, color, icon) in enumerate(secondary_specs):
            card = MetricCard(label, color, icon, compact=True)
            self.metrics[key] = card
            secondary_grid.addWidget(card, 0, i)
        self.layout.addLayout(secondary_grid)
        self.metrics["inscrits"].clicked.connect(lambda: self._goto_module(1))
        self.metrics["kiosque"].clicked.connect(lambda: self._goto_module(2))
        self.metrics["stock"].clicked.connect(lambda: self._goto_module(4))
        self.metrics["depenses"].clicked.connect(lambda: self._goto_module(3))
        self.metrics["recettes"].clicked.connect(lambda: self._goto_module(3))

    def _panel(self, title: str):
        panel = QFrame()
        panel.setStyleSheet(f"QFrame{{background:white;border:1px solid {COLORS['border']};border-radius:12px;}} QLabel{{background:transparent;border:none;}}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 13, 16, 14)
        label = QLabel(title)
        label.setStyleSheet("font-size:12px;font-weight:800;color:#334155;")
        layout.addWidget(label)
        return panel, layout

    def _build_activity(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        p1, l1 = self._panel("Derniers versements")
        self.payments_table = self._table(["Date", "Nom", "Scolarité", "Cantine", "Transport"], stretch_column=1)
        l1.addWidget(self.payments_table)
        row.addWidget(p1, 2)
        p2, l2 = self._panel("Dernières ventes")
        self.sales_table = self._table(["Date", "Article", "Qté", "Montant"], stretch_column=1)
        l2.addWidget(self.sales_table)
        row.addWidget(p2, 1)
        self.layout.addLayout(row)

    def _table(self, headers, stretch_column: int):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().hide()
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(len(headers)):
            mode = QHeaderView.Stretch if column == stretch_column else QHeaderView.ResizeToContents
            header.setSectionResizeMode(column, mode)
        table.setMaximumHeight(185)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"QTableWidget{{border:none;gridline-color:{COLORS['border_soft']};font-size:11px;alternate-background-color:#F8FAFC;}} QHeaderView::section{{background:#F1F5F9;border:none;padding:7px;font-weight:700;color:#475569;}}")
        return table

    def refresh_data(self, *_):
        period_key = self.PERIODS.get(self.period.currentText(), "year")
        data = DashboardV2Service.get_pilotage(period_key)
        self.activity_title.setText(f"INDICATEURS CLÉS · {self.period.currentText().upper()}")
        self.subtitle.setText(
            f"Année scolaire {DashboardService.get_active_school_year_label()}  ·  "
            f"{AppSession.get_logged_in_username()}  ·  dernière actualisation {datetime.now():%H:%M}"
        )
        for key in ("scolarite", "cantine", "transport"):
            self.recovery_cards[key].set_data(data[key])
        period_note = self.period.currentText().lower()
        new_label = "nouvel élève" if data["nouveaux"] == 1 else "nouveaux élèves"
        class_label = "classe" if data["classes"] == 1 else "classes"
        self.metrics["inscrits"].set_data(
            str(data["inscrits"]),
            f"{data['nouveaux']} {new_label} · {data['classes']} {class_label}",
        )
        solde_note = "Situation positive" if data["solde"] >= 0 else "Dépenses supérieures aux recettes"
        self.metrics["solde"].set_data(_money(data["solde"]), solde_note)
        self.metrics["recettes"].set_data(_money(data["recettes"]), f"Sur {period_note} · {data['operations']} opérations")
        self.metrics["depenses"].set_data(_money(data["depenses"]), f"Sur {period_note}")
        self.metrics["kiosque"].set_data(_money(data["kiosque"]), f"Sur {period_note}")
        self.metrics["stock"].set_data(_money(data["stock_value"]), f"{data['ruptures']} article(s) en rupture")
        self.metrics["autres"].set_data(_money(data["autres"]), f"Sur {period_note}")
        self.metrics["reductions"].set_data(_money(data["reductions"]), f"Sur {period_note}")
        self._fill_table(self.payments_table, DashboardService.get_latest_versements(), ["date", "eleve", "scolarite", "cantine", "transport"])
        self._fill_table(self.sales_table, DashboardService.get_latest_ventes(), ["date", "article", "quantite", "montant"])

    def _fill_table(self, table, rows, keys):
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(keys):
                item = QTableWidgetItem(str(row.get(key, "")))
                if key not in {"date", "eleve", "article"}:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if key in {"eleve", "article"}:
                    item.setToolTip(item.text())
                table.setItem(r, c, item)

    def _goto_module(self, original_index: int):
        if not self.main_window or not hasattr(self.main_window, "menu_list"):
            return
        for row in range(self.main_window.menu_list.count()):
            item = self.main_window.menu_list.item(row)
            if item.data(Qt.UserRole) == original_index:
                self.main_window.menu_list.setCurrentRow(row)
                return
