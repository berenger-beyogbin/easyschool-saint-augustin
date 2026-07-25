"""Widgets et delegate autonomes utilisés par MainWindow (views/main_window.py).

Regroupés ici car indépendants de l'état de MainWindow : chacun ne dépend
que de ses propres paramètres (et de app.styles.COLORS), jamais d'un
attribut de la fenêtre principale.
"""

import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QSize, QRect, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPainterPath, QPen

from app.styles import COLORS


class AvatarLabel(QLabel):
    """Label circulaire pour l'avatar utilisateur."""
    def __init__(self, initiales: str, parent=None):
        super().__init__(parent)
        self.initiales = initiales
        self.setFixedSize(46, 46)
        self.setStyleSheet("background-color: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(COLORS["primary"])))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 44, 44)
        painter.setPen(QColor("#FFFFFF"))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.initiales)
        painter.end()


class SMSPlaceholderWidget(QWidget):
    """Placeholder propre pour le module SMS."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        card = QFrame()
        card.setFixedWidth(480)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
                padding: 20px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel("✉")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"font-size: 48px; color: {COLORS['primary']}; background-color: transparent;"
        )

        title_lbl = QLabel("Module SMS")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['primary_dark']};"
            "background-color: transparent;"
        )

        badge = QLabel("BIENTÔT")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: #FFFFFF;"
            "font-size: 11px; font-weight: bold; border-radius: 10px;"
            "padding: 3px 14px; letter-spacing: 1px;"
        )
        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_row.addWidget(badge)
        badge_row.addStretch()

        desc_lbl = QLabel(
            "Cette fonctionnalité sera connectée ultérieurement.\n"
            "Elle permettra l'envoi de SMS groupés aux familles\n"
            "(rappels de versements, absences, convocations…)."
        )
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            f"font-size: 13px; color: {COLORS['muted']}; background-color: transparent; line-height: 1.6;"
        )

        card_layout.addWidget(icon_lbl)
        card_layout.addWidget(title_lbl)
        card_layout.addLayout(badge_row)
        card_layout.addSpacing(8)
        card_layout.addWidget(desc_lbl)

        layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch()


class SidebarItemDelegate(QStyledItemDelegate):
    """Dessine chaque item de la sidebar avec icône vectorielle uniforme (même taille, même trait)."""
    ITEM_H  = 52
    ICON_SZ = 18   # canvas icône en pixels

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        rect = option.rect
        orig = index.data(Qt.UserRole)
        row = orig if orig is not None else index.row()
        is_selected = bool(option.state & QStyle.State_Selected)
        is_hovered  = bool(option.state & QStyle.State_MouseOver)

        # Fond arrondi
        if is_selected or is_hovered:
            bg = QRectF(rect).adjusted(0, 2, 0, -2)
            path = QPainterPath()
            path.addRoundedRect(bg, 10, 10)
            fill = QColor(COLORS["primary"]) if is_selected else QColor(255, 255, 255, 18)
            painter.fillPath(path, QBrush(fill))

        # Indicateur barre verticale gauche (item actif)
        if is_selected:
            ind = QRectF(rect.left(), rect.top() + 10, 3, rect.height() - 20)
            p_ind = QPainterPath()
            p_ind.addRoundedRect(ind, 1.5, 1.5)
            painter.fillPath(p_ind, QBrush(QColor("#FFFFFF")))

        # Icône vectorielle
        icon_left = float(rect.left() + 16)
        cx = icon_left + self.ICON_SZ / 2.0
        cy = float(rect.center().y())
        icon_color = QColor("#FFFFFF") if is_selected else QColor("#94A3B8")
        self._draw_icon(painter, cx, cy, row, icon_color)

        # Étiquette
        label = index.data(Qt.DisplayRole) or ""
        label_x = int(icon_left + self.ICON_SZ + 12)
        label_rect = QRect(label_x, rect.top(), rect.right() - label_x - 6, rect.height())

        f_lbl = QFont("Segoe UI")
        f_lbl.setPixelSize(14)
        if is_selected:
            f_lbl.setWeight(QFont.Weight.DemiBold)
        painter.setFont(f_lbl)

        if row == 5:  # SMS — texte légèrement atténué
            painter.setPen(QColor("#64748B") if not is_selected else QColor("#B0BFCF"))
        else:
            painter.setPen(QColor("#FFFFFF") if is_selected else QColor("#CBD5E1"))

        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, label)

        # Badge "BIENTÔT" pour SMS
        if row == 5:
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(label)
            bx = float(label_x + tw + 8)
            by = float(rect.center().y()) - 9.0
            badge_r = QRectF(bx, by, 54, 18)
            painter.setBrush(QBrush(QColor(249, 115, 22, 210)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_r, 5, 5)
            f_badge = QFont("Segoe UI")
            f_badge.setPixelSize(10)
            f_badge.setBold(True)
            painter.setFont(f_badge)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(badge_r, Qt.AlignCenter, "BIENTÔT")

        painter.restore()

    # ------------------------------------------------------------------
    def _draw_icon(self, painter, cx, cy, row, color):
        """Dessine l'icône vectorielle centrée en (cx, cy) pour le menu row."""
        s = float(self.ICON_SZ)
        r = s / 2.0

        pen = QPen(color)
        pen.setWidthF(1.65)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if row == 0:  # Tableau de bord — grille 2×2
            sq = 7.0
            for dx, dy in [(-r + 0.5, -r + 0.5), (1.0, -r + 0.5),
                            (-r + 0.5,  1.0),      (1.0,  1.0)]:
                painter.drawRoundedRect(QRectF(cx + dx, cy + dy, sq, sq), 1.5, 1.5)

        elif row == 1:  # Scolarité — livre ouvert
            p = QPainterPath()
            p.moveTo(cx - 1.0, cy - r + 1)
            p.lineTo(cx - r + 1, cy - r + 3)
            p.lineTo(cx - r + 1, cy + r - 1)
            p.lineTo(cx - 1.0, cy + r - 1)
            painter.drawPath(p)
            p2 = QPainterPath()
            p2.moveTo(cx + 1.0, cy - r + 1)
            p2.lineTo(cx + r - 1, cy - r + 3)
            p2.lineTo(cx + r - 1, cy + r - 1)
            p2.lineTo(cx + 1.0, cy + r - 1)
            painter.drawPath(p2)
            painter.drawLine(QPointF(cx - 1.0, cy - r + 1), QPointF(cx + 1.0, cy - r + 1))
            painter.drawLine(QPointF(cx - 1.0, cy + r - 1), QPointF(cx + 1.0, cy + r - 1))

        elif row == 2:  # Kiosque — sac shopping
            painter.drawRoundedRect(QRectF(cx - r + 1, cy - 3.0, s - 2, r + 3), 2.5, 2.5)
            painter.drawArc(QRectF(cx - 4.5, cy - r + 1, 9, 9), 0, 180 * 16)

        elif row == 3:  # Comptabilité — histogramme 3 barres
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            bw, gap = 4.0, 2.5
            x0 = cx - (3 * bw + 2 * gap) / 2
            yb = cy + r - 1
            for i, bh in enumerate([r - 1, r + 3, r + 1]):
                painter.drawRoundedRect(QRectF(x0 + i * (bw + gap), yb - bh, bw, bh), 1, 1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

        elif row == 4:  # Statistiques — courbe ascendante + axes
            painter.drawLine(QPointF(cx - r + 1, cy + r - 1), QPointF(cx + r - 1, cy + r - 1))
            painter.drawLine(QPointF(cx - r + 1, cy - r + 1), QPointF(cx - r + 1, cy + r - 1))
            lc = QPainterPath()
            lc.moveTo(cx - r + 2, cy + 2)
            lc.lineTo(cx - 3, cy)
            lc.lineTo(cx + 1, cy - 3)
            lc.lineTo(cx + r - 2, cy - r + 3)
            painter.drawPath(lc)

        elif row == 5:  # SMS — bulle de message
            painter.drawRoundedRect(QRectF(cx - r + 1, cy - r + 1, s - 3, s - 5), 4, 4)
            tail = QPainterPath()
            tail.moveTo(cx - 3.5, cy + r - 4)
            tail.lineTo(cx - r + 2, cy + r - 1)
            tail.lineTo(cx - r + 6,  cy + r - 5)
            painter.drawPath(tail)

        elif row == 6:  # Paramètres — engrenage
            painter.drawEllipse(QRectF(cx - 3.5, cy - 3.5, 7, 7))
            for i in range(6):
                a = math.radians(i * 60 + 30)
                ca, sa = math.cos(a), math.sin(a)
                painter.drawLine(QPointF(cx + 4.5 * ca, cy + 4.5 * sa),
                                 QPointF(cx + r * ca,   cy + r * sa))

        elif row == 7:  # Utilisateurs — silhouette personne
            painter.drawEllipse(QRectF(cx - 4.0, cy - r + 1, 8, 8))
            painter.drawArc(QRectF(cx - r + 1, cy + 2, s - 3, r + 2), 0, 180 * 16)

    def sizeHint(self, option, index):
        return QSize(max(option.rect.width(), 200), self.ITEM_H)
