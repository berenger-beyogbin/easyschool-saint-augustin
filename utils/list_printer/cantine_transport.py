from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QPen, QColor, QPageSize, QPageLayout
from PySide6.QtCore import Qt, QRectF
import datetime

from ._common import C_BLACK, C_BORDER, C_HEADER_BG, C_ALT_ROW, C_NON_SOLDE, C_SOLDE, _font, _fmt_f


class CantineStatPrinter:
    """Impression A4 paysage de l'état des versements de cantine."""

    TITRE       = "ETAT DES VERSEMENTS DE LA CANTINE"
    COL_RATIOS  = [0.035, 0.090, 0.295, 0.085, 0.145, 0.145, 0.115, 0.090]
    COL_HEADERS = ["N°", "Matricule", "Élèves", "Classe", "Montant dû", "Versé", "Reste", "État"]
    COL_ALIGN   = ["C", "C", "L", "C", "R", "R", "R", "C"]

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
        sum_du = sum_vers = sum_reste = 0.0
        for idx, item in enumerate(rows):
            etat_raw = item.get("Etat", "Impayé")
            etat_lbl = "Soldé" if etat_raw == "Payé" else "Non soldé"

            du    = item.get("MontantDu", 0.0)
            vers  = item.get("MontantVerse", 0.0)
            reste = item.get("Reste", 0.0)

            sum_du    += du
            sum_vers  += vers
            sum_reste += reste

            formatted.append({
                "cells": [
                    str(idx + 1),
                    item.get("Matricule") or "",
                    (item.get("Nom") or "").upper(),
                    item.get("LibClasse") or "",
                    _fmt_f(du),
                    _fmt_f(vers),
                    _fmt_f(reste) if reste > 0 else "",
                    etat_lbl,
                ],
                "solde": etat_raw,
            })

        totaux = {"sum_du": sum_du, "sum_vers": sum_vers, "sum_reste": sum_reste}

        hdr_type = hdr_nom = hdr_tel = ""
        try:
            from services.etablissement_service import EtablissementService
            ecole = EtablissementService.get_etablissement()
            hdr_type = ecole.TypeEtab or ""
            hdr_nom  = ecole.RaisonSociale or ""
            hdr_tel  = ecole.Telephone or ""
        except Exception:
            pass

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(f"Aperçu — {cls.TITRE}")
        preview.resize(1100, 800)

        def _paint(p):
            cls._render(p, formatted, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre)

        preview.paintRequested.connect(_paint)
        preview.exec()

    @classmethod
    def _render(cls, printer, rows, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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
        HDR_H     = mm(34)
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
        etat_col   = len(cls.COL_HEADERS) - 1

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            Y = MT
            X = ML

            # ── En-tête école ───────────────────────────────────────────────
            painter.setPen(QPen(C_BLACK))
            painter.setFont(_font(8, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(5.5)), a_c | a_vc, hdr_type)
            Y += mm(6)

            painter.setFont(_font(15, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(10)), a_c | a_vc, hdr_nom)
            Y += mm(10.5)

            painter.setFont(_font(7.5))
            tel_line = f"CEL : {hdr_tel}" if hdr_tel else ""
            painter.drawText(QRectF(X, Y, CW, mm(5)), a_c | a_vc, tel_line)
            Y += mm(6.5)

            painter.setPen(QPen(C_BLACK, mm(0.3)))
            painter.drawLine(int(X), int(Y), int(X + CW), int(Y))
            Y += mm(2.5)

            title_text = cls.TITRE
            if titre_filtre:
                title_text += f"  —  {titre_filtre}"

            painter.setFont(_font(12, bold=True))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(QRectF(X, Y, CW * 0.78, mm(7.5)), a_vc | a_c, title_text)

            painter.setFont(_font(8))
            painter.drawText(QRectF(X + CW * 0.78, Y, CW * 0.22, mm(7.5)), a_vc | a_r, today_str)
            Y += mm(8.5)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(7, bold=True))

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

                painter.setFont(_font(6.8))
                cx = X
                for ci, (cell, cw, al) in enumerate(zip(row["cells"], COL_W, col_aligns)):
                    if ci == etat_col:
                        color = C_SOLDE if row["solde"] == "Payé" else C_NON_SOLDE
                        painter.setPen(QPen(color))
                    else:
                        painter.setPen(QPen(C_BLACK))
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

            # ── Totaux (dernière page uniquement) ────────────────────────────
            if page == total_pages - 1:
                ty = Y + len(page_rows) * ROW_H + mm(5)
                box_w = mm(58)
                box_x = X + CW - box_w
                line_h = mm(7)

                totaux_lines = [
                    ("Total Montant dû :",      _fmt_f(totaux["sum_du"])),
                    ("Total Montant versé :",   _fmt_f(totaux["sum_vers"])),
                    ("Total Montant restant :", _fmt_f(totaux["sum_reste"])),
                ]

                for label, value in totaux_lines:
                    painter.setPen(QPen(C_BORDER, mm(0.2)))
                    painter.setBrush(QColor(248, 250, 252))
                    painter.drawRect(QRectF(box_x, ty, box_w, line_h))

                    painter.setPen(QPen(C_BLACK))
                    painter.setFont(_font(7.5, bold=True))
                    painter.drawText(
                        QRectF(box_x + mm(2), ty, box_w * 0.6, line_h),
                        a_vc | a_l, label
                    )
                    painter.setFont(_font(8, bold=True))
                    painter.drawText(
                        QRectF(box_x + box_w * 0.55, ty, box_w * 0.42, line_h),
                        a_vc | a_r, value
                    )
                    ty += line_h + mm(1)

            # ── Pied de page ────────────────────────────────────────────────
            y_ftr = H - MB - FTR_H
            painter.setPen(QPen(C_BORDER, mm(0.2)))
            painter.drawLine(int(X), int(y_ftr), int(X + CW), int(y_ftr))

            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(_font(7))
            painter.drawText(
                QRectF(X, y_ftr + mm(1.5), CW, FTR_H - mm(1.5)),
                a_vc | a_r,
                f"{page + 1}/{total_pages}",
            )

        painter.end()


class TransportStatPrinter(CantineStatPrinter):
    """Impression A4 paysage de l'état des versements de transport."""

    TITRE = "ETAT DES VERSEMENTS DU TRANSPORT"


class InternatStatPrinter(CantineStatPrinter):
    """Impression A4 paysage de l'état financier de l'internat."""

    TITRE = "ETAT DES VERSEMENTS DE L'INTERNAT"
    COL_HEADERS = ["N°", "Matricule", "Pensionnaires", "Classe / origine", "Montant dû", "Versé", "Reste", "État"]


class CantineExterneStatPrinter(CantineStatPrinter):
    """Impression A4 paysage de l'état des versements de la cantine externe."""

    TITRE = "ETAT DES VERSEMENTS DE LA CANTINE EXTERNE"
    COL_HEADERS = ["N°", "Matricule", "Pensionnaires", "Responsable", "Montant dû", "Versé", "Reste", "État"]
