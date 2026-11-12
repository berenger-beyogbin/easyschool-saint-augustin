from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QPen, QColor, QPageSize, QPageLayout
from PySide6.QtCore import Qt, QRectF
import datetime

from ._common import C_BLACK, C_BORDER, C_HEADER_BG, C_ALT_ROW, _font, _fmt_f


class PeriodiqueStatPrinter:
    """Impression A4 portrait du récapitulatif des encaissements par rubrique sur une période."""

    TITRE       = "ETAT PERIODIQUE DES ENCAISSEMENTS"
    COL_RATIOS  = [0.65, 0.35]
    COL_HEADERS = ["Rubrique", "Montant"]
    COL_ALIGN   = ["L", "R"]

    @staticmethod
    def print_report(parent, rows: list, date_debut=None, date_fin=None):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        formatted = []
        sum_total = 0.0
        for item in rows:
            lib = item.get("Rubrique") or ""
            montant = item.get("Montant", 0.0)
            sum_total += montant
            formatted.append({"cells": [lib, _fmt_f(montant)]})

        totaux = {"sum_total": sum_total}

        hdr_type = hdr_nom = hdr_adresse = hdr_tel = ""
        try:
            from services.etablissement_service import EtablissementService
            ecole = EtablissementService.get_etablissement()
            hdr_type    = ecole.TypeEtab or ""
            hdr_nom     = ecole.RaisonSociale or ""
            hdr_adresse = ecole.Adresse or ""
            hdr_tel     = ecole.Telephone or ""
        except Exception:
            pass

        du_str = date_debut.strftime("%d/%m/%Y") if date_debut else ""
        au_str = date_fin.strftime("%d/%m/%Y") if date_fin else ""

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — État Périodique des Encaissements")
        preview.resize(820, 960)

        def _paint(p):
            PeriodiqueStatPrinter._render(
                p, formatted, totaux, hdr_type, hdr_nom, hdr_adresse, hdr_tel, du_str, au_str
            )

        preview.paintRequested.connect(_paint)
        preview.exec()

    @staticmethod
    def _render(printer, rows, totaux, hdr_type, hdr_nom, hdr_adresse, hdr_tel, du_str, au_str):
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        dpi = printer.resolution()

        def mm(v): return v * dpi / 25.4

        vp = painter.viewport()
        W, H = vp.width(), vp.height()

        ML, MR = mm(15), mm(15)
        MT, MB = mm(12), mm(12)
        CW = W - ML - MR

        ROW_H     = mm(9)
        COL_W     = [CW * r for r in PeriodiqueStatPrinter.COL_RATIOS]
        HDR_H     = mm(48)
        TBL_HDR_H = mm(9)
        FTR_H     = mm(20)

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
        col_aligns = [col_aligns_map[s] for s in PeriodiqueStatPrinter.COL_ALIGN]

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            Y = MT
            X = ML

            # ── En-tête école ───────────────────────────────────────────────
            painter.setPen(QPen(C_BLACK))
            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(6)), a_c | a_vc, hdr_type)
            Y += mm(6.5)

            painter.setFont(_font(16, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(11)), a_c | a_vc, hdr_nom)
            Y += mm(11)

            painter.setFont(_font(8))
            adr_line = " ".join(s for s in [
                f"{hdr_adresse}." if hdr_adresse else "",
                f"CEL : {hdr_tel}" if hdr_tel else "",
            ] if s)
            painter.drawText(QRectF(X, Y, CW, mm(5)), a_c | a_vc, adr_line)
            Y += mm(7)

            painter.setPen(QPen(C_BLACK, mm(0.35)))
            painter.drawLine(int(X), int(Y), int(X + CW), int(Y))
            Y += mm(3)

            # Titre + date du jour
            painter.setFont(_font(13, bold=True))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(QRectF(X, Y, CW * 0.72, mm(8)), a_vc | a_l, PeriodiqueStatPrinter.TITRE)

            painter.setFont(_font(8))
            painter.drawText(QRectF(X + CW * 0.72, Y, CW * 0.28, mm(8)), a_vc | a_r, today_str)
            Y += mm(9)

            # ── Période DU / AU ──────────────────────────────────────────────
            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X, Y, mm(14), mm(6)), a_vc | a_l, "DU")
            painter.setFont(_font(9))
            painter.drawText(QRectF(X + mm(15), Y, CW * 0.32, mm(6)), a_vc | a_l, du_str)

            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X + CW * 0.55, Y, mm(14), mm(6)), a_vc | a_l, "AU")
            painter.setFont(_font(9))
            painter.drawText(QRectF(X + CW * 0.55 + mm(15), Y, CW * 0.32, mm(6)), a_vc | a_l, au_str)
            Y += mm(9)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(9, bold=True))

            cx = X
            for lbl, cw, al in zip(PeriodiqueStatPrinter.COL_HEADERS, COL_W, col_aligns):
                pad_l = mm(2) if al == a_l else mm(1)
                painter.drawText(QRectF(cx + pad_l, Y, cw - mm(2), TBL_HDR_H), a_vc | al, lbl)
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

                painter.setFont(_font(9))
                painter.setPen(QPen(C_BLACK))
                cx = X
                for cell, cw, al in zip(row["cells"], COL_W, col_aligns):
                    pad_l = mm(2) if al == a_l else mm(1)
                    painter.drawText(QRectF(cx + pad_l, ry, cw - mm(2), ROW_H), a_vc | al, str(cell))
                    cx += cw

            table_h = TBL_HDR_H + len(page_rows) * ROW_H
            painter.setPen(QPen(C_BORDER, mm(0.28)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(X, Y - TBL_HDR_H, CW, table_h))

            cx = X
            for cw in COL_W[:-1]:
                cx += cw
                painter.setPen(QPen(C_BORDER, mm(0.12)))
                painter.drawLine(int(cx), int(Y - TBL_HDR_H), int(cx), int(Y - TBL_HDR_H + table_h))

            # ── Total général (dernière page uniquement) ─────────────────────
            if page == total_pages - 1:
                ty = Y + len(page_rows) * ROW_H + mm(8)
                box_w  = mm(65)
                box_x  = X + CW - box_w
                line_h = mm(9)

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(10, bold=True))
                painter.drawText(QRectF(box_x - mm(45), ty, mm(45), line_h), a_vc | a_l, "Total Général :")

                painter.setPen(QPen(C_BORDER, mm(0.25)))
                painter.setBrush(QColor(230, 230, 230))
                painter.drawRect(QRectF(box_x, ty, box_w, line_h))

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(10, bold=True))
                painter.drawText(QRectF(box_x, ty, box_w - mm(3), line_h), a_vc | a_r, _fmt_f(totaux["sum_total"]))

            # ── Pied de page ────────────────────────────────────────────────
            y_ftr = H - MB - mm(6)
            painter.setPen(QPen(QColor(100, 100, 100)))
            f_ftr = _font(8)
            f_ftr.setItalic(True)
            painter.setFont(f_ftr)
            painter.drawText(
                QRectF(X, y_ftr, CW, mm(6)),
                a_c | a_vc,
                f"{page + 1}/{total_pages}",
            )

        painter.end()
