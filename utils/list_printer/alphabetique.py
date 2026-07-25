from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QPen, QColor, QPageSize, QPageLayout, QPixmap
from PySide6.QtCore import Qt, QRectF
import datetime
import os

from ._common import C_BLACK, C_BORDER, C_HEADER_BG, C_ALT_ROW, _font


class ListeAlphabetiquePrinter:
    """Impression A4 paysage de la liste alphabétique des élèves d'une classe (document administratif officiel)."""

    TITRE       = "LISTE ALPHABETIQUE"
    COL_RATIOS  = [0.04, 0.12, 0.28, 0.12, 0.06, 0.22, 0.16]
    COL_HEADERS = ["N°", "Matricule", "Nom et Prénoms", "Date de Naissance",
                   "Sexe", "Profession", "Téléphone"]
    COL_ALIGN   = ["C", "C", "L", "C", "C", "L", "C"]

    REPUBLIQUE = "REPUBLIQUE DE COTE D'IVOIRE"
    DEVISE     = "Union - Discipline - Travail"

    @classmethod
    def print_report(cls, parent, rows: list, titre_filtre: str = ""):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setFullPage(True)

        formatted = []
        for idx, item in enumerate(rows):
            d_naiss = item["DateNaissance"].strftime("%d/%m/%Y") if item.get("DateNaissance") else ""
            noms    = f"{item.get('Nom', '')} {item.get('Prenoms', '')}".upper().strip()
            sexe    = "M" if item.get("Sexe") == 1 else "F"

            formatted.append([
                str(idx + 1),
                item.get("Matricule") or "",
                noms,
                d_naiss,
                sexe,
                item.get("Profession") or "",
                item.get("Telephone") or "",
            ])

        ecole = None
        try:
            from services.etablissement_service import EtablissementService
            ecole = EtablissementService.get_etablissement()
        except Exception:
            pass

        annee_libelle = AppSession.get_active_annee_libelle() or ""

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(f"Aperçu — {cls.TITRE}")
        preview.resize(1100, 800)

        def _paint(p):
            cls._render(p, formatted, ecole, annee_libelle, titre_filtre)

        preview.paintRequested.connect(_paint)
        preview.exec()

    # ------------------------------------------------------------------

    @classmethod
    def _render(cls, printer, rows, ecole, annee_libelle, titre_filtre):
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        dpi = printer.resolution()

        def mm(v): return v * dpi / 25.4

        vp = painter.viewport()
        W, H = vp.width(), vp.height()

        ML, MR = mm(12), mm(12)
        MT, MB = mm(10), mm(10)
        CW = W - ML - MR

        ROW_H     = mm(6.2)
        COL_W     = [CW * r for r in cls.COL_RATIOS]
        HDR_H     = mm(48)
        TBL_HDR_H = mm(7.5)
        FTR_H     = mm(7)

        BODY_H        = H - MT - MB - HDR_H - TBL_HDR_H - FTR_H
        ROWS_PER_PAGE = max(1, int(BODY_H / ROW_H))

        total_rows  = len(rows)
        total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        today_str   = datetime.date.today().strftime("%d/%m/%Y")

        a_c  = Qt.AlignmentFlag.AlignCenter
        a_l  = Qt.AlignmentFlag.AlignLeft
        a_r  = Qt.AlignmentFlag.AlignRight
        a_vc = Qt.AlignmentFlag.AlignVCenter

        col_aligns_map = {"C": a_c, "L": a_l, "R": a_r}
        col_aligns = [col_aligns_map[s] for s in cls.COL_ALIGN]

        ministere = (getattr(ecole, "Ministere", "") or "") if ecole else ""
        dren      = (getattr(ecole, "Dren", "") or "") if ecole else ""
        raison    = (getattr(ecole, "RaisonSociale", "") or "") if ecole else ""
        adresse   = (getattr(ecole, "Adresse", "") or "") if ecole else ""
        telephone = (getattr(ecole, "Telephone", "") or "") if ecole else ""
        slogan    = (getattr(ecole, "Slogan", "") or "") if ecole else ""
        logo_path = getattr(ecole, "LogoPath", None) if ecole else None

        logo_pix = None
        if logo_path:
            abs_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), logo_path)
            if os.path.isfile(abs_path):
                pix = QPixmap(abs_path)
                if not pix.isNull():
                    logo_pix = pix

        left_w  = CW * 0.62
        right_w = CW - left_w

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            Y = MT
            X = ML

            # ── En-tête administratif officiel (2 colonnes) ──────────────────
            painter.setPen(QPen(C_BLACK))

            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X, Y, left_w, mm(5)), a_l | a_vc, ministere)
            painter.drawText(QRectF(X + left_w, Y, right_w, mm(5)), a_r | a_vc, cls.REPUBLIQUE)
            Y += mm(5.5)

            dren_line = f"Direction Régionale de l'Education Nationale  {dren}".strip()
            painter.setFont(_font(8.5, bold=True))
            painter.drawText(QRectF(X, Y, left_w, mm(5)), a_l | a_vc, dren_line)
            painter.setFont(_font(8))
            painter.drawText(QRectF(X + left_w, Y, right_w, mm(5)), a_r | a_vc, cls.DEVISE)
            Y += mm(5.5)

            painter.setFont(_font(10, bold=True))
            painter.drawText(QRectF(X, Y, left_w, mm(6)), a_l | a_vc, raison)
            Y += mm(6.5)

            logo_y = Y
            logo_size = mm(16)
            if logo_pix is not None:
                scaled = logo_pix.scaled(int(logo_size), int(logo_size),
                                          Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(int(X), int(logo_y), scaled)
                text_x = X + logo_size + mm(3)
                text_w = left_w - logo_size - mm(3)
            else:
                text_x = X
                text_w = left_w

            painter.setFont(_font(8))
            painter.drawText(QRectF(text_x, logo_y, text_w, mm(5)), a_l | a_vc, adresse)
            painter.drawText(QRectF(text_x, logo_y + mm(5), text_w, mm(5)), a_l | a_vc, f"Tél : {telephone}")

            if slogan:
                f = _font(7.5)
                f.setItalic(True)
                painter.setFont(f)
                painter.drawText(QRectF(text_x, logo_y + mm(10), text_w, mm(5)), a_l | a_vc, slogan)

            painter.setFont(_font(8.5, bold=True))
            painter.drawText(QRectF(X + left_w, logo_y, right_w, mm(5)), a_r | a_vc,
                              f"Année scolaire : {annee_libelle}")

            Y = logo_y + logo_size + mm(2)

            # ── Titre encadré ─────────────────────────────────────────────────
            title_h = mm(9)
            title_text = cls.TITRE
            if titre_filtre:
                title_text += f" : {titre_filtre}"
            painter.setPen(QPen(C_BLACK, mm(0.3)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(X, Y, CW, title_h))
            painter.setFont(_font(11, bold=True))
            painter.drawText(QRectF(X, Y, CW, title_h), a_c | a_vc, title_text)
            Y += title_h + mm(3)

            # ── Champ Maître (à remplir à la main) ──────────────────────────
            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X, Y, mm(20), mm(6)), a_l | a_vc, "Maître :")
            painter.setPen(QPen(C_BORDER, mm(0.2)))
            painter.drawLine(int(X + mm(20)), int(Y + mm(5)), int(X + mm(90)), int(Y + mm(5)))
            Y += mm(8)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(7.5, bold=True))

            cx = X
            for lbl, cw, al in zip(cls.COL_HEADERS, COL_W, col_aligns):
                pad_l = mm(1.5) if al == a_l else mm(0.5)
                painter.drawText(QRectF(cx + pad_l, Y, cw - mm(1), TBL_HDR_H), a_vc | al, lbl)
                cx += cw
            Y += TBL_HDR_H

            # ── Lignes de données ───────────────────────────────────────────
            start = page * ROWS_PER_PAGE
            end   = min(start + ROWS_PER_PAGE, total_rows)
            page_rows = rows[start:end]

            for li, row in enumerate(page_rows):
                ry = Y + li * ROW_H
                if li % 2 == 1:
                    painter.fillRect(QRectF(X, ry, CW, ROW_H), C_ALT_ROW)

                painter.setPen(QPen(C_BORDER, mm(0.12)))
                painter.drawLine(int(X), int(ry + ROW_H), int(X + CW), int(ry + ROW_H))

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(7.5))
                cx = X
                for cell, cw, al in zip(row, COL_W, col_aligns):
                    pad_l = mm(1.5) if al == a_l else mm(0.5)
                    painter.drawText(QRectF(cx + pad_l, ry, cw - mm(1), ROW_H), a_vc | al, str(cell))
                    cx += cw

            table_h = TBL_HDR_H + len(page_rows) * ROW_H
            painter.setPen(QPen(C_BORDER, mm(0.25)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(X, Y - TBL_HDR_H, CW, table_h))

            cx = X
            for cw in COL_W[:-1]:
                cx += cw
                painter.setPen(QPen(C_BORDER, mm(0.12)))
                painter.drawLine(int(cx), int(Y - TBL_HDR_H), int(cx), int(Y - TBL_HDR_H + table_h))

            # ── Pied de page ────────────────────────────────────────────────
            y_ftr = H - MB - FTR_H
            painter.setPen(QPen(C_BORDER, mm(0.2)))
            painter.drawLine(int(X), int(y_ftr), int(X + CW), int(y_ftr))

            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(_font(7.5))
            painter.drawText(
                QRectF(X, y_ftr + mm(1.5), CW * 0.5, FTR_H - mm(1.5)),
                a_vc | a_l,
                f"Edité le : {today_str}",
            )
            painter.drawText(
                QRectF(X + CW * 0.5, y_ftr + mm(1.5), CW * 0.5, FTR_H - mm(1.5)),
                a_vc | a_r,
                f"{page + 1}/{total_pages}",
            )

        painter.end()
