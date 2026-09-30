from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QPen, QColor, QPageSize, QPageLayout
from PySide6.QtCore import Qt, QRectF
import datetime

from ._common import C_BLACK, C_BORDER, C_HEADER_BG, C_ALT_ROW, _font


class InscritsListPrinter:
    """Impression A4 portrait multi-pages de la liste des inscrits."""

    COL_RATIOS  = [0.05, 0.12, 0.12, 0.12, 0.47, 0.12]
    COL_HEADERS = ["N°", "Inscrit le", "Matricule", "Né(e) le", "Noms", "Classe"]
    COL_ALIGN   = ["C", "C", "C", "C", "L", "C"]
    TITRE       = "LISTE DES INSCRITS"
    PREVIEW_TITRE = "Aperçu — Liste des Inscrits"

    @staticmethod
    def format_row(idx: int, item: dict) -> list:
        d_insc = item["DateInscription"].strftime("%d/%m/%Y") if item.get("DateInscription") else ""
        matr   = item.get("Matricule") or ""
        d_nais = item["DateNaissance"].strftime("%d/%m/%Y") if item.get("DateNaissance") else ""
        noms   = f"{item.get('Nom', '')} {item.get('Prenoms', '')}".upper().strip()
        classe = item.get("LibClasse") or ""
        return [str(idx + 1), d_insc, matr, d_nais, noms, classe]

    @classmethod
    def print_list(cls, parent, rows: list, titre_filtre: str = ""):
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

        formatted = [cls.format_row(idx, item) for idx, item in enumerate(rows)]

        # Infos école
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
        preview.setWindowTitle(cls.PREVIEW_TITRE)
        preview.resize(820, 960)

        def _paint(p):
            cls._render(
                p, formatted, hdr_type, hdr_nom, hdr_tel, titre_filtre
            )

        preview.paintRequested.connect(_paint)
        preview.exec()

    # ------------------------------------------------------------------

    @classmethod
    def _render(cls, printer, rows, hdr_type, hdr_nom, hdr_tel, titre_filtre):
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
        COL_W     = [CW * r for r in cls.COL_RATIOS]
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

        _al = {"C": a_center, "L": a_left, "R": a_right}
        col_aligns = [_al[c] for c in cls.COL_ALIGN]

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
            title_text = cls.TITRE
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
            for lbl, cw, al in zip(cls.COL_HEADERS, COL_W, col_aligns):
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


class _ListePensionnairesPrinter(InscritsListPrinter):
    """Liste nominative sans montants (internat / cantine externe)."""

    COL_RATIOS  = [0.06, 0.16, 0.48, 0.30]
    COL_ALIGN   = ["C", "C", "L", "C"]

    @staticmethod
    def format_row(idx: int, item: dict) -> list:
        return [
            str(idx + 1), item.get("Matricule") or "",
            (item.get("Nom") or "").upper().strip(), item.get("LibClasse") or "",
        ]


class InternatListPrinter(_ListePensionnairesPrinter):
    TITRE = "LISTE DES PENSIONNAIRES DE L'INTERNAT"
    PREVIEW_TITRE = "Aperçu — Liste de l'internat"
    COL_HEADERS = ["N°", "Matricule", "Noms", "Classe / origine"]


class CantineExterneListPrinter(_ListePensionnairesPrinter):
    TITRE = "LISTE DES PENSIONNAIRES DE LA CANTINE EXTERNE"
    PREVIEW_TITRE = "Aperçu — Liste de la cantine externe"
    COL_HEADERS = ["N°", "Matricule", "Noms", "Responsable"]
