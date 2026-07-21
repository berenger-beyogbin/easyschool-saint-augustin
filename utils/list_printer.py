from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPageSize, QPageLayout, QPixmap
from PySide6.QtCore import Qt, QRectF
import datetime
import os

from utils.print_helpers import (
    format_fcfa,
    get_etablissement_print_info,
    payment_status_label,
)

C_BLACK      = QColor(0,   0,   0)
C_BORDER     = QColor(180, 180, 180)
C_HEADER_BG  = QColor(30,  41,  59)   # slate-800
C_ALT_ROW    = QColor(248, 250, 252)  # slate-50
C_NON_SOLDE  = QColor(220,  38,  38)  # red-600
C_SOLDE      = QColor(22,  163,  74)  # green-600
C_WARNING    = QColor(249, 115,  22)  # orange-600


def _payment_status_color(status):
    if status == "Payé":
        return C_SOLDE
    if status == "Partiel":
        return C_WARNING
    return C_NON_SOLDE


def _font(size_pt: float, bold: bool = False) -> QFont:
    f = QFont("Arial", size_pt)
    f.setBold(bold)
    return f


class InscritsListPrinter:
    """Impression A4 portrait multi-pages de la liste des inscrits."""

    COL_RATIOS  = [0.05, 0.12, 0.12, 0.12, 0.47, 0.12]
    COL_HEADERS = ["N°", "Inscrit le", "Matricule", "Né(e) le", "Noms", "Classe"]
    COL_ALIGN   = ["C", "C", "C", "C", "L", "C"]

    @staticmethod
    def print_list(parent, rows: list, titre_filtre: str = ""):
        """
        rows : liste de dicts avec clés DateInscription, Matricule, Nom,
               Prenoms, DateNaissance, LibClasse
        """
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        # Formater les données
        formatted = []
        for idx, item in enumerate(rows):
            d_insc = item["DateInscription"].strftime("%d/%m/%Y") if item.get("DateInscription") else ""
            matr   = item.get("Matricule") or ""
            d_nais = item["DateNaissance"].strftime("%d/%m/%Y") if item.get("DateNaissance") else ""
            noms   = f"{item.get('Nom', '')} {item.get('Prenoms', '')}".upper().strip()
            classe = item.get("LibClasse") or ""
            formatted.append([str(idx + 1), d_insc, matr, d_nais, noms, classe])

        # Infos école
        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — Liste des Inscrits")
        preview.resize(820, 960)

        def _paint(p):
            InscritsListPrinter._render(
                p, formatted, hdr_type, hdr_nom, hdr_tel, titre_filtre
            )

        preview.paintRequested.connect(_paint)
        preview.exec()

    # ------------------------------------------------------------------

    @staticmethod
    def _render(printer, rows, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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

        ROW_H     = mm(6.5)
        COL_W     = [CW * r for r in InscritsListPrinter.COL_RATIOS]
        HDR_H     = mm(38)
        TBL_HDR_H = mm(8)
        FTR_H     = mm(8)

        BODY_H        = H - MT - MB - HDR_H - TBL_HDR_H - FTR_H
        ROWS_PER_PAGE = max(1, int(BODY_H / ROW_H))

        total_rows  = len(rows)
        total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
        today_str   = datetime.date.today().strftime("%d/%m/%Y")

        a_center = Qt.AlignmentFlag.AlignCenter
        a_left   = Qt.AlignmentFlag.AlignLeft
        a_right  = Qt.AlignmentFlag.AlignRight
        a_vcenter = Qt.AlignmentFlag.AlignVCenter

        col_aligns = [a_center, a_center, a_center, a_center, a_left, a_center]

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            Y = MT
            X = ML

            # ── En-tête école ───────────────────────────────────────────────
            painter.setPen(QPen(C_BLACK))

            painter.setFont(_font(9, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(6)),
                             a_center | a_vcenter, hdr_type)
            Y += mm(6.5)

            painter.setFont(_font(16, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(11)),
                             a_center | a_vcenter, hdr_nom)
            Y += mm(11)

            painter.setFont(_font(8))
            tel_line = f"CEL : {hdr_tel}" if hdr_tel else ""
            painter.drawText(QRectF(X, Y, CW, mm(5)),
                             a_center | a_vcenter, tel_line)
            Y += mm(7)

            # Séparateur horizontal
            painter.setPen(QPen(C_BLACK, mm(0.35)))
            painter.drawLine(int(X), int(Y), int(X + CW), int(Y))
            Y += mm(3)

            # Titre du rapport + date
            title_text = "LISTE DES INSCRITS"
            if titre_filtre:
                title_text += f"  —  {titre_filtre}"

            painter.setFont(_font(13, bold=True))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(QRectF(X, Y, CW * 0.72, mm(8)),
                             a_vcenter | a_left, title_text)

            painter.setFont(_font(8))
            painter.drawText(QRectF(X + CW * 0.72, Y, CW * 0.28, mm(8)),
                             a_vcenter | a_right, today_str)
            Y += mm(8)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(8, bold=True))

            cx = X
            for lbl, cw, al in zip(InscritsListPrinter.COL_HEADERS, COL_W, col_aligns):
                pad = mm(1.5) if al == a_left else mm(0.5)
                painter.drawText(QRectF(cx + pad, Y, cw - mm(1), TBL_HDR_H),
                                 a_vcenter | al, lbl)
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
                for ci, (cell, cw, al) in enumerate(zip(row, COL_W, col_aligns)):
                    pad = mm(1.5) if al == a_left else mm(0.5)
                    painter.drawText(QRectF(cx + pad, ry, cw - mm(1), ROW_H),
                                     a_vcenter | al, str(cell))
                    cx += cw

            # Cadre + séparateurs verticaux du tableau
            table_h = TBL_HDR_H + len(page_rows) * ROW_H
            painter.setPen(QPen(C_BORDER, mm(0.28)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(X, Y - TBL_HDR_H, CW, table_h))

            cx = X
            for cw in COL_W[:-1]:
                cx += cw
                painter.setPen(QPen(C_BORDER, mm(0.12)))
                painter.drawLine(int(cx), int(Y - TBL_HDR_H),
                                 int(cx), int(Y - TBL_HDR_H + table_h))

            # ── Pied de page ─────────────────────────────────────────────────
            y_ftr = H - MB - FTR_H
            painter.setPen(QPen(C_BORDER, mm(0.2)))
            painter.drawLine(int(X), int(y_ftr), int(X + CW), int(y_ftr))

            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(_font(7.5))
            painter.drawText(
                QRectF(X, y_ftr + mm(1.5), CW, FTR_H - mm(1.5)),
                a_vcenter | a_right,
                f"Page {page + 1} / {total_pages}    —    Total : {total_rows} inscrits",
            )

        painter.end()


# ---------------------------------------------------------------------------
# État des Versements de Scolarité — impression A4 paysage
# ---------------------------------------------------------------------------

def _fmt_f(montant) -> str:
    return format_fcfa(montant)


class ScolariteStatPrinter:
    """Impression A4 paysage multi-pages de l'état des versements de scolarité."""

    COL_RATIOS  = [0.035, 0.090, 0.270, 0.080, 0.130, 0.130, 0.090, 0.090, 0.085]
    COL_HEADERS = ["N°", "Matricule", "Élèves", "Classe",
                   "Montant dû", "Versé", "Red.", "Reste", "État"]
    COL_ALIGN   = ["C", "C", "L", "C", "R", "R", "R", "R", "C"]

    @staticmethod
    def print_report(parent, rows: list, titre_filtre: str = ""):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setFullPage(True)

        # Formater les données
        formatted = []
        sum_du = sum_vers = sum_reduc = sum_reste = 0.0
        for idx, item in enumerate(rows):
            etat_raw = item.get("Etat", "Impayé")
            etat_lbl = payment_status_label(etat_raw)

            du    = item.get("MontantDu", 0.0)
            vers  = item.get("MontantVerse", 0.0)
            reduc = item.get("Reduction", 0.0)
            reste = item.get("Reste", 0.0)

            sum_du    += du
            sum_vers  += vers
            sum_reduc += reduc
            sum_reste += reste

            formatted.append({
                "cells": [
                    str(idx + 1),
                    item.get("Matricule") or "",
                    (item.get("Nom") or "").upper(),
                    item.get("LibClasse") or "",
                    _fmt_f(du),
                    _fmt_f(vers),
                    _fmt_f(reduc) if reduc > 0 else "",
                    _fmt_f(reste) if reste > 0 else "",
                    etat_lbl,
                ],
                "solde": etat_raw,
            })

        totaux = {
            "sum_du":    sum_du,
            "sum_vers":  sum_vers,
            "sum_reduc": sum_reduc,
            "sum_reste": sum_reste,
        }

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — État des Versements de Scolarité")
        preview.resize(1100, 800)

        def _paint(p):
            ScolariteStatPrinter._render(
                p, formatted, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre
            )

        preview.paintRequested.connect(_paint)
        preview.exec()

    # ------------------------------------------------------------------

    @staticmethod
    def _render(printer, rows, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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
        COL_W     = [CW * r for r in ScolariteStatPrinter.COL_RATIOS]
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
        col_aligns = [col_aligns_map[s] for s in ScolariteStatPrinter.COL_ALIGN]

        for page in range(total_pages):
            if page > 0:
                printer.newPage()

            Y = MT
            X = ML

            # ── En-tête école ───────────────────────────────────────────────
            painter.setPen(QPen(C_BLACK))

            painter.setFont(_font(8, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(5.5)),
                             a_c | a_vc, hdr_type)
            Y += mm(6)

            painter.setFont(_font(15, bold=True))
            painter.drawText(QRectF(X, Y, CW, mm(10)),
                             a_c | a_vc, hdr_nom)
            Y += mm(10.5)

            painter.setFont(_font(7.5))
            tel_line = f"CEL : {hdr_tel}" if hdr_tel else ""
            painter.drawText(QRectF(X, Y, CW, mm(5)),
                             a_c | a_vc, tel_line)
            Y += mm(6.5)

            painter.setPen(QPen(C_BLACK, mm(0.3)))
            painter.drawLine(int(X), int(Y), int(X + CW), int(Y))
            Y += mm(2.5)

            # Titre + date
            title_text = "ETAT DES VERSEMENTS DE LA SCOLARITE"
            if titre_filtre:
                title_text += f"  —  {titre_filtre}"

            painter.setFont(_font(12, bold=True))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(QRectF(X, Y, CW * 0.78, mm(7.5)),
                             a_vc | a_c, title_text)

            painter.setFont(_font(8))
            painter.drawText(QRectF(X + CW * 0.78, Y, CW * 0.22, mm(7.5)),
                             a_vc | a_r, today_str)
            Y += mm(8.5)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(7, bold=True))

            cx = X
            for lbl, cw, al in zip(ScolariteStatPrinter.COL_HEADERS, COL_W, col_aligns):
                pad_l = mm(1.5) if al == a_l else mm(0.5)
                painter.drawText(QRectF(cx + pad_l, Y, cw - mm(1), TBL_HDR_H),
                                 a_vc | al, lbl)
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
                etat_col = len(ScolariteStatPrinter.COL_HEADERS) - 1
                for ci, (cell, cw, al) in enumerate(zip(row["cells"], COL_W, col_aligns)):
                    if ci == etat_col:
                        color = _payment_status_color(row["solde"])
                        painter.setPen(QPen(color))
                    else:
                        painter.setPen(QPen(C_BLACK))
                    pad_l = mm(1.5) if al == a_l else mm(0.5)
                    painter.drawText(QRectF(cx + pad_l, ry, cw - mm(1), ROW_H),
                                     a_vc | al, str(cell))
                    cx += cw

            # Cadre + séparateurs verticaux
            table_h = TBL_HDR_H + len(page_rows) * ROW_H
            painter.setPen(QPen(C_BORDER, mm(0.25)))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(X, Y - TBL_HDR_H, CW, table_h))

            cx = X
            for cw in COL_W[:-1]:
                cx += cw
                painter.setPen(QPen(C_BORDER, mm(0.12)))
                painter.drawLine(int(cx), int(Y - TBL_HDR_H),
                                 int(cx), int(Y - TBL_HDR_H + table_h))

            # ── Totaux (dernière page uniquement) ────────────────────────────
            if page == total_pages - 1:
                ty = Y + len(page_rows) * ROW_H + mm(5)
                box_w = mm(58)
                box_x = X + CW - box_w
                line_h = mm(7)

                totaux_lines = [
                    ("Total Montant dû :",    _fmt_f(totaux["sum_du"])),
                    ("Total Montant versé :", _fmt_f(totaux["sum_vers"])),
                    ("Réduction :",           _fmt_f(totaux["sum_reduc"])),
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
            etat_lbl = payment_status_label(etat_raw)

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

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

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
                        color = _payment_status_color(row["solde"])
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


class VenteStatPrinter:
    """Impression A4 portrait de l'état des ventes au kiosque."""

    TITRE       = "ETAT DES VENTES AU KIOSQUE"
    COL_RATIOS  = [0.16, 0.44, 0.16, 0.24]
    COL_HEADERS = ["Date", "Article", "Quantité", "Prix"]
    COL_ALIGN   = ["C", "L", "C", "R"]

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
            d   = item["DateSort"].strftime("%d/%m/%Y") if item.get("DateSort") else ""
            art = item.get("Article") or ""
            qty = str(item.get("QuantiteSort", ""))
            tot = item.get("Total", 0.0)

            sum_total += tot

            formatted.append({
                "cells": [d, art, qty, _fmt_f(tot)],
            })

        totaux = {"sum_total": sum_total}

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_adresse = etablissement.adresse
        hdr_tel = etablissement.telephone

        du_str = date_debut.strftime("%d/%m/%Y") if date_debut else ""
        au_str = date_fin.strftime("%d/%m/%Y") if date_fin else ""

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — État des Ventes au Kiosque")
        preview.resize(820, 960)

        def _paint(p):
            VenteStatPrinter._render(
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

        ROW_H     = mm(7)
        COL_W     = [CW * r for r in VenteStatPrinter.COL_RATIOS]
        HDR_H     = mm(48)
        TBL_HDR_H = mm(8)
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
        col_aligns = [col_aligns_map[s] for s in VenteStatPrinter.COL_ALIGN]

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
            painter.drawText(QRectF(X, Y, CW * 0.72, mm(8)), a_vc | a_l, VenteStatPrinter.TITRE)

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
            painter.setFont(_font(8, bold=True))

            cx = X
            for lbl, cw, al in zip(VenteStatPrinter.COL_HEADERS, COL_W, col_aligns):
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

                painter.setFont(_font(7.5))
                painter.setPen(QPen(C_BLACK))
                cx = X
                for cell, cw, al in zip(row["cells"], COL_W, col_aligns):
                    pad_l = mm(1.5) if al == a_l else mm(0.5)
                    painter.drawText(QRectF(cx + pad_l, ry, cw - mm(1), ROW_H), a_vc | al, str(cell))
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

            # ── Signature / Total (dernière page uniquement) ─────────────────
            if page == total_pages - 1:
                sig_y = Y + len(page_rows) * ROW_H + mm(10)

                painter.save()
                painter.translate(X + mm(20), sig_y + mm(8))
                painter.rotate(-8)
                painter.setPen(QPen(C_BLACK))
                f_italic = _font(10)
                f_italic.setItalic(True)
                painter.setFont(f_italic)
                painter.drawText(QRectF(-mm(20), -mm(6), mm(60), mm(6)), a_c, "Merci")
                painter.drawText(QRectF(-mm(20), mm(1), mm(60), mm(6)), a_c, "Bonne Année Scolaire !")
                painter.restore()

                box_w  = mm(60)
                box_x  = X + CW - box_w
                line_h = mm(8)
                ty     = sig_y

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(9, bold=True))
                painter.drawText(QRectF(box_x - mm(28), ty, mm(28), line_h), a_vc | a_l, "Total Vendu :")

                painter.setPen(QPen(C_BORDER, mm(0.25)))
                painter.setBrush(QColor(230, 230, 230))
                painter.drawRect(QRectF(box_x, ty, box_w, line_h))

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(9, bold=True))
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


class StockStatPrinter:
    """Impression A4 paysage de l'état du stock kiosque."""

    TITRE       = "ETAT DU STOCK KIOSQUE"
    COL_RATIOS  = [0.035, 0.380, 0.160, 0.110, 0.155, 0.160]
    COL_HEADERS = ["N°", "Article", "Prix Unitaire", "Seuil", "Stock Courant", "État"]
    COL_ALIGN   = ["C", "L", "R", "C", "C", "C"]

    _C_ALERTE = QColor(217, 119, 6)   # amber-600

    @staticmethod
    def print_report(parent, rows: list, titre_filtre: str = ""):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setFullPage(True)

        formatted = []
        sum_valeur = 0.0
        for idx, item in enumerate(rows):
            lib = item.get("Libelle") or ""
            if item.get("KIT"):
                lib += " (KIT)"
            pu     = item.get("PU", 0.0)
            seuil  = str(item.get("QTESeuil", 0))
            qty    = str(item.get("QuantiteCour", 0))
            valeur = item.get("ValeurStock", 0.0)
            etat   = item.get("Etat", "OK")

            sum_valeur += valeur

            formatted.append({
                "cells": [str(idx + 1), lib, _fmt_f(pu), seuil, qty, etat],
                "etat":  etat,
            })

        totaux = {"sum_valeur": sum_valeur}

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — État du Stock Kiosque")
        preview.resize(1100, 800)

        def _paint(p):
            StockStatPrinter._render(p, formatted, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre)

        preview.paintRequested.connect(_paint)
        preview.exec()

    @staticmethod
    def _render(printer, rows, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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
        COL_W     = [CW * r for r in StockStatPrinter.COL_RATIOS]
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
        col_aligns = [col_aligns_map[s] for s in StockStatPrinter.COL_ALIGN]
        etat_col   = len(StockStatPrinter.COL_HEADERS) - 1

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

            title_text = StockStatPrinter.TITRE
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
            for lbl, cw, al in zip(StockStatPrinter.COL_HEADERS, COL_W, col_aligns):
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
                        etat = row["etat"]
                        if etat == "Rupture":
                            painter.setPen(QPen(C_NON_SOLDE))
                        elif etat == "Alerte":
                            painter.setPen(QPen(StockStatPrinter._C_ALERTE))
                        else:
                            painter.setPen(QPen(C_SOLDE))
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

                painter.setPen(QPen(C_BORDER, mm(0.2)))
                painter.setBrush(QColor(248, 250, 252))
                painter.drawRect(QRectF(box_x, ty, box_w, line_h))

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(7.5, bold=True))
                painter.drawText(QRectF(box_x + mm(2), ty, box_w * 0.6, line_h),
                                 a_vc | a_l, "Valeur globale valorisée :")
                painter.setFont(_font(8, bold=True))
                painter.drawText(QRectF(box_x + box_w * 0.55, ty, box_w * 0.42, line_h),
                                 a_vc | a_r, _fmt_f(totaux["sum_valeur"]))

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


class PrestationSyntheseStatPrinter:
    """Impression A4 paysage de la synthèse par classe/prestation (ventilation analytique)."""

    TITRE       = "ETAT DE VENTILATION DES PRESTATIONS — SYNTHESE PAR CLASSE"
    COL_RATIOS  = [0.220, 0.260, 0.110, 0.150, 0.150, 0.110]
    COL_HEADERS = ["Classe", "Prestation", "Nb élèves",
                   "Montant théorique", "Montant ventilé", "Reste"]
    COL_ALIGN   = ["L", "L", "C", "R", "R", "R"]

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
        sum_nb = 0
        sum_theo = sum_ventile = sum_reste = 0.0
        for row in rows:
            nb      = row.get("nb_eleves", 0)
            theo    = row.get("total_theorique", 0.0)
            ventile = row.get("total_ventile", 0.0)
            reste   = row.get("reste", 0.0)

            sum_nb      += nb
            sum_theo    += theo
            sum_ventile += ventile
            sum_reste   += reste

            formatted.append({
                "cells": [
                    row.get("classe") or "",
                    row.get("prestation") or "",
                    str(nb),
                    _fmt_f(theo),
                    _fmt_f(ventile),
                    _fmt_f(reste) if reste > 0 else "",
                ],
                "reste": reste,
            })

        totaux = {
            "sum_nb": sum_nb, "sum_theo": sum_theo,
            "sum_ventile": sum_ventile, "sum_reste": sum_reste,
        }

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

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
        reste_col  = len(cls.COL_HEADERS) - 1

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

            painter.setFont(_font(11, bold=True))
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
                    if ci == reste_col and row["reste"] > 0:
                        painter.setPen(QPen(C_WARNING))
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
                box_w = mm(62)
                box_x = X + CW - box_w
                line_h = mm(7)

                totaux_lines = [
                    ("Nombre d'élèves :",         str(totaux["sum_nb"])),
                    ("Total montant théorique :", _fmt_f(totaux["sum_theo"])),
                    ("Total montant ventilé :",   _fmt_f(totaux["sum_ventile"])),
                    ("Total reste à recouvrer :", _fmt_f(totaux["sum_reste"])),
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


class PrestationDetailStatPrinter:
    """Impression A4 paysage du détail par élève (ventilation analytique des prestations)."""

    TITRE       = "ETAT DE VENTILATION DES PRESTATIONS — DETAIL PAR ELEVE"
    COL_RATIOS  = [0.110, 0.290, 0.110, 0.190, 0.110, 0.110, 0.090]
    COL_HEADERS = ["Matricule", "Nom & Prénoms", "Classe", "Prestation",
                   "Mnt théorique", "Mnt ventilé", "Reste"]
    COL_ALIGN   = ["C", "L", "C", "L", "R", "R", "R"]

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
        sum_theo = sum_ventile = sum_reste = 0.0
        for row in rows:
            theo    = row.get("montant_theorique", 0.0)
            ventile = row.get("montant_ventile", 0.0)
            reste   = row.get("reste", 0.0)

            sum_theo    += theo
            sum_ventile += ventile
            sum_reste   += reste

            formatted.append({
                "cells": [
                    row.get("matricule") or "",
                    (row.get("nom") or "").upper(),
                    row.get("classe") or "",
                    row.get("prestation") or "",
                    _fmt_f(theo),
                    _fmt_f(ventile),
                    _fmt_f(reste) if reste > 0 else "",
                ],
                "reste": reste,
            })

        totaux = {"sum_theo": sum_theo, "sum_ventile": sum_ventile, "sum_reste": sum_reste}

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom = etablissement.nom
        hdr_tel = etablissement.telephone

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
        reste_col  = len(cls.COL_HEADERS) - 1

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

            painter.setFont(_font(11, bold=True))
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
                    if ci == reste_col and row["reste"] > 0:
                        painter.setPen(QPen(C_WARNING))
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
                box_w = mm(62)
                box_x = X + CW - box_w
                line_h = mm(7)

                totaux_lines = [
                    ("Total montant théorique :", _fmt_f(totaux["sum_theo"])),
                    ("Total montant ventilé :",   _fmt_f(totaux["sum_ventile"])),
                    ("Total reste à recouvrer :", _fmt_f(totaux["sum_reste"])),
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

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        ecole = etablissement.etablissement

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
            abs_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), logo_path)
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


class BalanceComptesPrinter:
    """Impression A4 paysage de la balance des comptes (débit/crédit/solde)."""

    TITRE       = "BALANCE DES COMPTES"
    COL_RATIOS  = [0.13, 0.42, 0.15, 0.15, 0.15]
    COL_HEADERS = ["N° Compte", "Compte", "Débit", "Crédit", "Solde"]
    COL_ALIGN   = ["C", "L", "R", "R", "R"]

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
        sum_debit = sum_credit = sum_solde = 0.0
        for item in rows:
            debit = item.get("Debit", 0.0)
            credit = item.get("Credit", 0.0)
            solde = item.get("Solde", 0.0)

            sum_debit  += debit
            sum_credit += credit
            sum_solde  += solde

            formatted.append({
                "cells": [
                    item.get("NumCompte") or "",
                    item.get("LibCompte") or "",
                    format_fcfa(debit),
                    format_fcfa(credit),
                    format_fcfa(solde),
                ],
                "solde": solde,
            })

        totaux = {"sum_debit": sum_debit, "sum_credit": sum_credit, "sum_solde": sum_solde}

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom  = etablissement.nom
        hdr_tel  = etablissement.telephone

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
        solde_col  = len(cls.COL_HEADERS) - 1

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
                    if ci == solde_col:
                        if row["solde"] < 0:
                            painter.setPen(QPen(C_NON_SOLDE))
                        elif row["solde"] > 0:
                            painter.setPen(QPen(C_SOLDE))
                        else:
                            painter.setPen(QPen(C_BLACK))
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
                    ("Total Débit :", format_fcfa(totaux["sum_debit"])),
                    ("Total Crédit :", format_fcfa(totaux["sum_credit"])),
                    ("Solde global :", format_fcfa(totaux["sum_solde"])),
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


class EtatSortiesPrinter:
    """Impression A4 portrait de l'état des sorties (mouvements de dépense)."""

    TITRE       = "ETAT DES SORTIES"
    COL_RATIOS  = [0.14, 0.34, 0.16, 0.16, 0.20]
    COL_HEADERS = ["Date", "Bénéficiaire", "Téléphone", "Montant", "Compte"]
    COL_ALIGN   = ["C", "L", "C", "R", "L"]

    @staticmethod
    def print_report(parent, rows: list, titre_filtre: str = ""):
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
            montant = item.get("Montant", 0.0)
            sum_total += montant
            formatted.append({
                "cells": [
                    item.get("Date") or "",
                    item.get("Beneficiaire") or "",
                    item.get("Telephone") or "",
                    format_fcfa(montant),
                    item.get("Compte") or "",
                ],
            })

        totaux = {"sum_total": sum_total}

        etablissement = get_etablissement_print_info(parent)
        if etablissement is None:
            return
        hdr_type = etablissement.type_etablissement
        hdr_nom  = etablissement.nom
        hdr_tel  = etablissement.telephone

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(f"Aperçu — {EtatSortiesPrinter.TITRE}")
        preview.resize(820, 960)

        def _paint(p):
            EtatSortiesPrinter._render(
                p, formatted, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre
            )

        preview.paintRequested.connect(_paint)
        preview.exec()

    @staticmethod
    def _render(printer, rows, totaux, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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

        ROW_H     = mm(6.5)
        COL_W     = [CW * r for r in EtatSortiesPrinter.COL_RATIOS]
        HDR_H     = mm(38)
        TBL_HDR_H = mm(8)
        FTR_H     = mm(16)

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
        col_aligns = [col_aligns_map[s] for s in EtatSortiesPrinter.COL_ALIGN]

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
            tel_line = f"CEL : {hdr_tel}" if hdr_tel else ""
            painter.drawText(QRectF(X, Y, CW, mm(5)), a_c | a_vc, tel_line)
            Y += mm(7)

            painter.setPen(QPen(C_BLACK, mm(0.35)))
            painter.drawLine(int(X), int(Y), int(X + CW), int(Y))
            Y += mm(3)

            title_text = EtatSortiesPrinter.TITRE
            if titre_filtre:
                title_text += f"  —  {titre_filtre}"

            painter.setFont(_font(13, bold=True))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(QRectF(X, Y, CW * 0.72, mm(8)), a_vc | a_l, title_text)

            painter.setFont(_font(8))
            painter.drawText(QRectF(X + CW * 0.72, Y, CW * 0.28, mm(8)), a_vc | a_r, today_str)
            Y += mm(9)

            # ── En-tête colonnes ────────────────────────────────────────────
            painter.fillRect(QRectF(X, Y, CW, TBL_HDR_H), C_HEADER_BG)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(_font(8, bold=True))

            cx = X
            for lbl, cw, al in zip(EtatSortiesPrinter.COL_HEADERS, COL_W, col_aligns):
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
                for cell, cw, al in zip(row["cells"], COL_W, col_aligns):
                    pad_l = mm(1.5) if al == a_l else mm(0.5)
                    painter.drawText(QRectF(cx + pad_l, ry, cw - mm(1), ROW_H), a_vc | al, str(cell))
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

            # ── Total (dernière page uniquement) ─────────────────────────────
            if page == total_pages - 1:
                ty = Y + len(page_rows) * ROW_H + mm(5)
                box_w = mm(64)
                box_x = X + CW - box_w
                line_h = mm(8)

                painter.setPen(QPen(C_BLACK))
                painter.setFont(_font(9, bold=True))
                painter.drawText(QRectF(box_x - mm(46), ty, mm(46), line_h),
                                  a_vc | a_l, "Total Général des Sorties :")

                painter.setPen(QPen(C_BORDER, mm(0.25)))
                painter.setBrush(QColor(230, 230, 230))
                painter.drawRect(QRectF(box_x, ty, box_w, line_h))

                painter.setPen(QPen(C_NON_SOLDE))
                painter.setFont(_font(9, bold=True))
                painter.drawText(QRectF(box_x, ty, box_w - mm(3), line_h),
                                  a_vc | a_r, format_fcfa(totaux["sum_total"]))

            # ── Pied de page ────────────────────────────────────────────────
            y_ftr = H - MB - FTR_H
            painter.setPen(QPen(C_BORDER, mm(0.2)))
            painter.drawLine(int(X), int(y_ftr), int(X + CW), int(y_ftr))

            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(_font(7.5))
            painter.drawText(
                QRectF(X, y_ftr + mm(1.5), CW, FTR_H - mm(1.5)),
                a_vc | a_r,
                f"{page + 1}/{total_pages}",
            )

        painter.end()
