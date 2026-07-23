import math
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTabWidget, QComboBox,
    QMessageBox, QFrame, QScrollArea, QPushButton, QSizePolicy,
    QStyledItemDelegate, QStyle
)
from PySide6.QtCore import Qt, QSize, QRect, QRectF, QPointF
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPainterPath, QPen

# Import des fiches du module Parametres
from .etablissement_view import EtablissementView
from .annee_scolaire_view import AnneeScolaireView
from .cycle_view import CycleView
from .niveau_view import NiveauView
from .classe_view import ClasseView
from .nationalite_view import NationaliteView
from .religion_view import ReligionView
from .scolarite_view import ScolariteView
from .kiosque_view import KiosqueView
from .comptabilite_view import ComptabiliteView
from .statistiques_view import StatistiquesView
from .dashboard_switcher_view import DashboardSwitcherView
from .utilisateurs_view import UtilisateursView
from .prestation_config_view import PrestationConfigView

from app.styles import (
    COLORS, SIDEBAR_MENU_STYLE, TAB_STYLE, COMBO_STYLE, BUTTON_SECONDARY
)


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
            p.moveTo(cx - 1.0, cy - r + 1); p.lineTo(cx - r + 1, cy - r + 3)
            p.lineTo(cx - r + 1, cy + r - 1); p.lineTo(cx - 1.0, cy + r - 1)
            painter.drawPath(p)
            p2 = QPainterPath()
            p2.moveTo(cx + 1.0, cy - r + 1); p2.lineTo(cx + r - 1, cy - r + 3)
            p2.lineTo(cx + r - 1, cy + r - 1); p2.lineTo(cx + 1.0, cy + r - 1)
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
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)

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


class MainWindow(QMainWindow):
    """Fenêtre principale Easy School 2.0 — Template UI Moderne."""

    # (label, code_permission) — ordre original figé pour les icônes
    MENU_ITEMS = [
        ("Tableau de bord", "DASHBOARD_VIEW"),
        ("Scolarité",       "SCOLARITE_VIEW"),
        ("Kiosque",         "KIOSQUE_VIEW"),
        ("Comptabilité",    "COMPTABILITE_VIEW"),
        ("Statistiques",    "STATISTIQUES_VIEW"),
        ("SMS",             "SMS_VIEW"),
        ("Paramètres",      "PARAMETRES_VIEW"),
        ("Utilisateurs",    "UTILISATEURS_VIEW"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Easy School 2.0 — Gestion d'École Professionnelle")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)
        self.init_ui()

    # =========================================================================
    # CONSTRUCTION UI
    # =========================================================================

    def init_ui(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        layout_principal.addWidget(self._build_sidebar())
        layout_principal.addWidget(self._build_workspace(), 1)

        # Activer Tableau de bord au démarrage
        self.menu_list.setCurrentRow(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS['sidebar_bg']};
                min-width: 235px;
                max-width: 235px;
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Logo ---
        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar_bg_2']};
                border-bottom: 1px solid rgba(255,255,255,0.07);
                padding: 0;
            }}
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(18, 20, 18, 20)
        logo_layout.setSpacing(0)

        logo_title_row = QHBoxLayout()
        logo_title_row.setSpacing(8)
        logo_title_row.setContentsMargins(0, 0, 0, 0)

        lbl_logo_top = QLabel("Easy School")
        lbl_logo_top.setStyleSheet(
            "color: #FFFFFF; font-size: 18px; font-weight: bold;"
            "background-color: transparent; letter-spacing: 0.2px;"
        )
        logo_title_row.addWidget(lbl_logo_top)

        lbl_logo_sub = QLabel("2.0")
        lbl_logo_sub.setStyleSheet(
            f"color: #FFFFFF; background-color: {COLORS['primary']}; font-size: 11px;"
            "font-weight: bold; border-radius: 5px; padding: 1px 6px;"
        )
        lbl_logo_sub.setFixedHeight(20)
        logo_title_row.addWidget(lbl_logo_sub, 0, Qt.AlignVCenter)
        logo_title_row.addStretch()

        logo_layout.addLayout(logo_title_row)
        layout.addWidget(logo_frame)

        # --- Bloc Utilisateur (dynamique depuis AppSession) ---
        from app.session import AppSession
        _user_nom = AppSession.get_current_user_nom() or "Administrateur"
        _user_role = AppSession.get_current_user_profil_libelle() or "Administrateur"
        _initiales = "".join(p[0].upper() for p in _user_nom.split()[:2]) or "AD"

        user_frame = QFrame()
        user_frame.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,0.04); border: none; }"
        )
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(16, 14, 16, 14)
        user_layout.setSpacing(12)

        self.avatar = AvatarLabel(_initiales)
        user_layout.addWidget(self.avatar)

        user_info = QVBoxLayout()
        user_info.setSpacing(3)
        user_info.setContentsMargins(0, 0, 0, 0)

        lbl_user_name = QLabel(_user_nom.upper())
        lbl_user_name.setStyleSheet(
            "color: #FFFFFF; font-size: 13px; font-weight: bold;"
            " background-color: transparent; border: none;"
        )

        lbl_user_role = QLabel(_user_role)
        lbl_user_role.setStyleSheet(
            "color: #94A3B8; font-size: 11px; background-color: transparent; border: none;"
        )

        lbl_status = QLabel("● En ligne")
        lbl_status.setStyleSheet(
            "color: #4ADE80; font-size: 11px; background-color: transparent; border: none;"
        )

        user_info.addWidget(lbl_user_name)
        user_info.addWidget(lbl_user_role)
        user_info.addWidget(lbl_status)
        user_layout.addLayout(user_info)
        user_layout.addStretch()

        layout.addWidget(user_frame)

        # --- Séparateur ---
        sep_lbl = QLabel("NAVIGATION")
        sep_lbl.setStyleSheet(
            "color: rgba(255,255,255,225.25); font-size: 10px; font-weight: 700;"
            "letter-spacing: 2px; background-color: transparent;"
        )
        sep_wrap = QFrame()
        sep_wrap.setStyleSheet("background-color: transparent;")
        sep_wrap_layout = QHBoxLayout(sep_wrap)
        sep_wrap_layout.setContentsMargins(18, 12, 18, 4)
        sep_wrap_layout.addWidget(sep_lbl)
        layout.addWidget(sep_wrap)

        # --- Menu de navigation ---
        self.menu_list = QListWidget()
        self.menu_list.setStyleSheet(SIDEBAR_MENU_STYLE)
        self.menu_list.setFocusPolicy(Qt.NoFocus)
        self.menu_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for orig_idx, (label, perm) in enumerate(self.MENU_ITEMS):
            if AppSession.has_permission(perm):
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, orig_idx)
                self.menu_list.addItem(item)

        self.menu_list.setItemDelegate(SidebarItemDelegate(self.menu_list))
        self.menu_list.currentRowChanged.connect(self.navigation_menu_changed)

        menu_wrap = QFrame()
        menu_wrap.setStyleSheet("background-color: transparent;")
        menu_wrap_layout = QVBoxLayout(menu_wrap)
        menu_wrap_layout.setContentsMargins(10, 6, 10, 6)
        menu_wrap_layout.setSpacing(0)
        menu_wrap_layout.addWidget(self.menu_list)
        layout.addWidget(menu_wrap, 1)

        # --- Version en bas ---
        sep_bottom = QFrame()
        sep_bottom.setFrameShape(QFrame.HLine)
        sep_bottom.setStyleSheet("color: rgba(255,255,255,0.07);")
        layout.addWidget(sep_bottom)

        lbl_version = QLabel("Version 2.0 — 2026 © Easy School")
        lbl_version.setStyleSheet(
            "color: rgba(255,255,255,0.25); font-size: 10px; background-color: transparent;"
        )
        lbl_version.setAlignment(Qt.AlignCenter)

        ver_wrap = QFrame()
        ver_wrap.setStyleSheet("background-color: transparent;")
        ver_layout = QVBoxLayout(ver_wrap)
        ver_layout.setContentsMargins(0, 8, 0, 12)
        ver_layout.addWidget(lbl_version)
        layout.addWidget(ver_wrap)

        return sidebar

    def _build_workspace(self) -> QFrame:
        workspace = QFrame()
        workspace.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Topbar ---
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setStyleSheet(f"""
            QFrame#topbar {{
                background-color: {COLORS['card']};
                border-bottom: 1px solid {COLORS['border']};
                min-height: 58px;
                max-height: 58px;
            }}
        """)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(24, 0, 24, 0)
        topbar_layout.setSpacing(12)

        # Titre module
        self.lbl_module_titre = QLabel("MODULE EN COURS : TABLEAU DE BORD")
        self.lbl_module_titre.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLORS['text']};"
            "background-color: transparent;"
        )

        topbar_layout.addWidget(self.lbl_module_titre)
        topbar_layout.addStretch()

        # Sélecteur année scolaire
        lbl_annee = QLabel("Année Académique :")
        lbl_annee.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 12px; font-weight: 500;"
            "background-color: transparent;"
        )

        self.cmb_annee_header = QComboBox()
        self.cmb_annee_header.setFixedWidth(140)
        self.cmb_annee_header.setStyleSheet(COMBO_STYLE)

        self.load_annees_in_header()
        self.cmb_annee_header.currentIndexChanged.connect(self.on_annee_header_changed)

        topbar_layout.addWidget(lbl_annee)
        topbar_layout.addWidget(self.cmb_annee_header)

        # Séparateur vertical
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setFixedHeight(22)
        sep_v.setStyleSheet(f"color: {COLORS['border']}; margin: 0 4px;")
        topbar_layout.addWidget(sep_v)

        # Bouton sélection imprimante
        btn_imprimante = QPushButton("Imprimante")
        btn_imprimante.setStyleSheet(BUTTON_SECONDARY)
        btn_imprimante.setFixedHeight(34)
        btn_imprimante.setMinimumWidth(110)
        btn_imprimante.setToolTip("Choisir l'imprimante par défaut pour les reçus")
        btn_imprimante.clicked.connect(self._open_printer_dialog)
        topbar_layout.addWidget(btn_imprimante)

        layout.addWidget(topbar)

        # --- Stack des modules ---
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg']};")

        # index 0: Tableau de bord
        self.widget_dashboard = DashboardSwitcherView(self)
        self.stack.addWidget(self.widget_dashboard)

        # index 1: Paramètres
        self.widget_parametres = QWidget()
        self.widget_parametres.setStyleSheet(f"background-color: {COLORS['bg']};")
        self.setup_parametres_tab()
        self.stack.addWidget(self.widget_parametres)

        # index 2: Scolarité
        self.widget_scolarite = ScolariteView(self)
        self.stack.addWidget(self.widget_scolarite)

        # index 3: Kiosque
        self.widget_kiosque = KiosqueView(self)
        self.stack.addWidget(self.widget_kiosque)

        # index 4: Comptabilité
        self.widget_comptabilite = ComptabiliteView(self)
        self.stack.addWidget(self.widget_comptabilite)

        # index 5: Statistiques
        self.widget_statistiques = StatistiquesView(self)
        self.stack.addWidget(self.widget_statistiques)

        # index 6: SMS placeholder
        self.widget_sms = SMSPlaceholderWidget(self)
        self.stack.addWidget(self.widget_sms)

        # index 7: Utilisateurs
        self.widget_utilisateurs = UtilisateursView(self)
        self.stack.addWidget(self.widget_utilisateurs)

        layout.addWidget(self.stack)
        return workspace

    # =========================================================================
    # SETUP PARAMÈTRES
    # =========================================================================

    def setup_parametres_tab(self):
        layout_param_base = QVBoxLayout(self.widget_parametres)
        layout_param_base.setContentsMargins(16, 16, 16, 16)

        self.tab_parametres_onglets = QTabWidget()
        self.tab_parametres_onglets.setStyleSheet(TAB_STYLE)

        # Onglet 1 : Généraux
        tab_generaux = QTabWidget()
        tab_generaux.setTabPosition(QTabWidget.West)
        tab_generaux.setStyleSheet(TAB_STYLE)
        tab_generaux.addTab(EtablissementView(), "Établissement")

        self.annee_view = AnneeScolaireView()
        self.annee_view.data_changed.connect(self.reload_annee_header)
        tab_generaux.addTab(self.annee_view, "Année Scolaire")

        support_lbl = QLabel(
            "Support Technique :\nContactez Julien Kanga au 01-xx-xx-xx-xx."
        )
        support_lbl.setAlignment(Qt.AlignCenter)
        support_lbl.setStyleSheet(
            f"color: {COLORS['muted']}; font-size: 13px; padding: 30px;"
        )
        tab_generaux.addTab(support_lbl, "Support Technique")
        tab_generaux.currentChanged.connect(self.refresh_active_view)

        # Onglet 2 : Classes
        tab_classes = QTabWidget()
        tab_classes.setTabPosition(QTabWidget.West)
        tab_classes.setStyleSheet(TAB_STYLE)
        tab_classes.addTab(CycleView(), "Cycle")
        tab_classes.addTab(NiveauView(), "Niveau")
        tab_classes.addTab(ClasseView(), "Classe")
        tab_classes.currentChanged.connect(self.refresh_active_view)

        # Onglet 4 : Autres réglages
        tab_autres = QTabWidget()
        tab_autres.setTabPosition(QTabWidget.West)
        tab_autres.setStyleSheet(TAB_STYLE)
        tab_autres.addTab(NationaliteView(), "Nationalités")
        tab_autres.addTab(ReligionView(), "Religions")
        tab_autres.currentChanged.connect(self.refresh_active_view)

        # Onglet 5 : Prestations annexes
        self.prestation_config_view = PrestationConfigView(self)

        self.tab_parametres_onglets.addTab(tab_generaux, "Généraux")
        self.tab_parametres_onglets.addTab(tab_classes, "Classes")
        self.tab_parametres_onglets.addTab(tab_autres, "Autres réglages")
        self.tab_parametres_onglets.addTab(self.prestation_config_view, "Prestations")
        self.tab_parametres_onglets.currentChanged.connect(self.refresh_active_view)

        layout_param_base.addWidget(self.tab_parametres_onglets)

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def navigation_menu_changed(self, index):
        """Active l'écran correspondant selon le menu latéral sélectionné."""
        item = self.menu_list.item(index)
        orig = item.data(Qt.UserRole) if item else index

        titles = {
            0: "TABLEAU DE BORD",
            1: "SCOLARITÉ / INSCRIPTIONS",
            2: "KIOSQUE & BIBLIOTHÈQUE",
            3: "COMPTABILITÉ FINANCIÈRE",
            4: "STATISTIQUES ET RAPPORTS",
            5: "SMS  ·  BIENTÔT",
            6: "PARAMÈTRES",
            7: "GESTION DES UTILISATEURS",
        }
        label = titles.get(orig, "")
        primary_color = COLORS["primary"]
        self.lbl_module_titre.setText(
            f"MODULE EN COURS :  <span style='color:{primary_color};'>{label}</span>"
        )
        self.lbl_module_titre.setTextFormat(Qt.RichText)

        if orig == 0:
            if hasattr(self.widget_dashboard, "refresh_data"):
                self.widget_dashboard.refresh_data()
            self.stack.setCurrentIndex(0)
        elif orig == 6:
            self.stack.setCurrentIndex(1)
        elif orig == 1:
            if hasattr(self.widget_scolarite, "on_sub_tab_changed"):
                self.widget_scolarite.on_sub_tab_changed(
                    self.widget_scolarite.sub_tabs.currentIndex()
                )
            self.stack.setCurrentIndex(2)
        elif orig == 2:
            if hasattr(self.widget_kiosque, "load_data"):
                self.widget_kiosque.load_data()
            self.stack.setCurrentIndex(3)
        elif orig == 3:
            if hasattr(self.widget_comptabilite, "load_data"):
                self.widget_comptabilite.load_data()
            self.stack.setCurrentIndex(4)
        elif orig == 4:
            if hasattr(self.widget_statistiques, "refresh_data"):
                self.widget_statistiques.refresh_data()
            self.stack.setCurrentIndex(5)
        elif orig == 5:
            self.stack.setCurrentIndex(6)
        elif orig == 7:
            if hasattr(self.widget_utilisateurs, "refresh_data"):
                self.widget_utilisateurs.refresh_data()
            self.stack.setCurrentIndex(7)

    def _open_printer_dialog(self):
        from views.imprimante_dialog import ImprimanteDialog
        dlg = ImprimanteDialog(self)
        dlg.exec()

    def reload_annee_header(self):
        """Recharge le sélecteur d'année scolaire après création ou clôture."""
        self.load_annees_in_header()
        self.refresh_active_view()

    def close_active_tab(self):
        """Revient au tableau de bord (index 0)."""
        self.menu_list.setCurrentRow(0)

    def refresh_active_view(self, index=None):
        """Actualise la vue active dans Paramètres."""
        curr_widget = self.tab_parametres_onglets.currentWidget()
        if isinstance(curr_widget, QTabWidget):
            active_view = curr_widget.currentWidget()
        else:
            active_view = curr_widget

        if active_view and hasattr(active_view, "refresh_data"):
            try:
                active_view.refresh_data()
            except Exception as e:
                print(f"Erreur rafraîchissement vue {active_view} : {e}")

    # =========================================================================
    # ANNÉE SCOLAIRE HEADER
    # =========================================================================

    def load_annees_in_header(self):
        from services.annee_scolaire_service import AnneeScolaireService
        from app.session import AppSession

        AppSession.initialize_session()

        annees = AnneeScolaireService.get_all()
        display_list = [a for a in annees if not a.Cloturer]
        if not display_list:
            AppSession._active_annee_id = None
            AppSession._active_annee_libelle = None
            AppSession.initialize_session()
            annees = AnneeScolaireService.get_all()
            display_list = [a for a in annees if not a.Cloturer]

        self.cmb_annee_header.blockSignals(True)
        self.cmb_annee_header.clear()

        for annee in display_list:
            self.cmb_annee_header.addItem(annee.Libelle, annee.IDTAnneeScolaire)

        active_id = AppSession.get_active_annee_id()
        idx = self.cmb_annee_header.findData(active_id)
        if idx >= 0:
            self.cmb_annee_header.setCurrentIndex(idx)
        elif self.cmb_annee_header.count() > 0:
            self.cmb_annee_header.setCurrentIndex(0)
            current_id = self.cmb_annee_header.currentData()
            current_libelle = self.cmb_annee_header.currentText()
            AppSession.set_active_annee(current_id, current_libelle)

        self.cmb_annee_header.blockSignals(False)

    def on_annee_header_changed(self, index=None):
        from app.session import AppSession
        current_id = self.cmb_annee_header.currentData()
        current_libelle = self.cmb_annee_header.currentText()
        if current_id:
            AppSession.set_active_annee(current_id, current_libelle)

            curr_idx = self.stack.currentIndex()
            if curr_idx == 1:
                self.refresh_active_view()
            elif curr_idx == 2:
                if hasattr(self.widget_scolarite, "on_sub_tab_changed"):
                    self.widget_scolarite.on_sub_tab_changed(
                        self.widget_scolarite.sub_tabs.currentIndex()
                    )
            elif curr_idx == 3:
                if hasattr(self.widget_kiosque, "load_data"):
                    self.widget_kiosque.load_data()
            elif curr_idx == 4:
                if hasattr(self.widget_comptabilite, "load_data"):
                    self.widget_comptabilite.load_data()
