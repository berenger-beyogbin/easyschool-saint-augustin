from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPageSize, QPageLayout
from PySide6.QtCore import Qt, QRectF

# ── En-tête école : fallback neutre si aucun établissement n'est trouvé ───────
_HDR_NOM_FALLBACK = "ÉTABLISSEMENT SCOLAIRE"

# ── Palette ───────────────────────────────────────────────────────────────────
C_BLACK  = QColor(0,   0,   0)
C_BORDER = QColor(160, 160, 160)
C_BLUE   = QColor(37,  99,  235)
C_GREEN  = QColor(22,  163,  74)
C_ORANGE = QColor(194,  65,  12)
C_MUTED  = QColor(130, 130, 130)


def _fmt(v) -> str:
    try:
        return f"{int(float(v)):,} F".replace(",", " ")
    except Exception:
        return "0 F"


def _font(size_pt: float, bold: bool = False) -> QFont:
    f = QFont("Arial", size_pt)
    f.setBold(bold)
    return f


class ReceiptPrinter:
    """Reçu de paiement — A5 paysage. Libellés à gauche, 3 colonnes de valeurs."""

    @staticmethod
    def print_receipt(parent, data: dict):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        from app.session import AppSession
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)

        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A5))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setFullPage(True)

        hdr = ReceiptPrinter._get_etablissement_header()

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — Reçu de paiement")
        preview.resize(980, 700)
        preview.paintRequested.connect(lambda p: ReceiptPrinter._render(p, data, hdr))
        preview.exec()

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_etablissement_header() -> dict:
        """Recupere les infos d'en-tete de l'etablissement pour le recu.
        Ne doit jamais lever d'exception : un recu doit toujours pouvoir s'imprimer."""
        hdr = {
            "type": "", "nom": _HDR_NOM_FALLBACK, "sigle": "",
            "adresse": "", "telephone": "", "email": "", "slogan": "",
            "dren": "", "iep": "",
        }
        try:
            from services.etablissement_service import EtablissementService
            ecole = EtablissementService.get_etablissement()
            hdr["type"]      = ecole.TypeEtab or ""
            hdr["nom"]       = ecole.RaisonSociale or _HDR_NOM_FALLBACK
            hdr["sigle"]     = ecole.Sigle or ""
            hdr["adresse"]   = ecole.Adresse or ""
            hdr["telephone"] = ecole.Telephone or ""
            hdr["email"]     = ecole.Email or ""
            hdr["slogan"]    = ecole.Slogan or ""
            hdr["dren"]      = ecole.Dren or ""
            hdr["iep"]       = ecole.IEP or ""
        except Exception:
            pass
        return hdr

    @staticmethod
    def _render(printer: QPrinter, data: dict, hdr: dict = None):
        if hdr is None:
            hdr = ReceiptPrinter._get_etablissement_header()
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        dpi = printer.resolution()

        def mm(v: float) -> float:
            return v * dpi / 25.4

        vp = painter.viewport()
        W, H = vp.width(), vp.height()

        ML, MT = mm(10), mm(8)
        MR, MB = mm(10), mm(8)
        X, Y = ML, MT
        CW = W - ML - MR
        CH = H - MT - MB

        # ── CADRE DOUBLE ─────────────────────────────────────────────────────
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(C_BLACK, mm(0.45)))
        painter.drawRect(QRectF(X, Y, CW, CH))
        painter.setPen(QPen(C_BORDER, mm(0.12)))
        painter.drawRect(QRectF(X + mm(1.2), Y + mm(1.2), CW - mm(2.4), CH - mm(2.4)))

        # Marques de coin
        mk, gp = mm(4), mm(3)
        painter.setPen(QPen(C_BLACK, mm(0.28)))
        for cx, cy, dx, dy in [(0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)]:
            painter.drawLine(int(cx + dx * gp), int(cy), int(cx + dx * (gp + mk)), int(cy))
            painter.drawLine(int(cx), int(cy + dy * gp), int(cx), int(cy + dy * (gp + mk)))

        # ── EN-TÊTE (dynamique, selon l'établissement enregistré) ─────────────
        painter.setPen(QPen(C_BLACK))

        hdr_line1 = "  —  ".join(s for s in [hdr.get("type", ""), hdr.get("dren", ""), hdr.get("iep", "")] if s)
        hdr_line2 = hdr.get("nom") or _HDR_NOM_FALLBACK
        if hdr.get("sigle"):
            hdr_line2 = f"{hdr_line2} ({hdr['sigle']})"
        hdr_line3_parts = [hdr.get("adresse", "")]
        if hdr.get("telephone"):
            hdr_line3_parts.append(f"CEL : {hdr['telephone']}")
        if hdr.get("email"):
            hdr_line3_parts.append(hdr["email"])
        if hdr.get("slogan"):
            hdr_line3_parts.append(f"« {hdr['slogan']} »")
        hdr_line3 = "  —  ".join(s for s in hdr_line3_parts if s)

        painter.setFont(_font(9, bold=True))
        painter.drawText(
            QRectF(X, Y + mm(2.5), CW, mm(7)),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            hdr_line1,
        )

        painter.setFont(_font(20, bold=True))
        painter.drawText(
            QRectF(X, Y + mm(8), CW, mm(12)),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            hdr_line2,
        )

        painter.setFont(_font(8, bold=True))
        painter.drawText(
            QRectF(X, Y + mm(19), CW, mm(6)),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            hdr_line3,
        )

        # Ligne fine sous l'en-tête
        y_sep1 = Y + mm(26)
        painter.setPen(QPen(C_BLACK, mm(0.22)))
        painter.drawLine(int(X + mm(1.5)), int(y_sep1), int(X + CW - mm(1.5)), int(y_sep1))

        # ── INFOS ÉLÈVE ───────────────────────────────────────────────────────
        y_info = y_sep1 + mm(2)
        row_h = mm(6)
        painter.setFont(_font(9, bold=True))
        painter.setPen(QPen(C_BLACK))

        painter.drawText(QRectF(X + mm(3), y_info, CW * 0.43, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Date :  {data.get('date', '')}")
        painter.drawText(QRectF(X + CW * 0.47, y_info, CW * 0.5, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Matricule :  {data.get('matricule', '')}")

        y_info += row_h
        painter.drawText(QRectF(X + mm(3), y_info, CW - mm(4), row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Noms :  {data.get('nom', '')}")

        y_info += row_h
        painter.drawText(QRectF(X + mm(3), y_info, CW * 0.43, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Classe :  {data.get('classe', '')}")
        painter.drawText(QRectF(X + CW * 0.47, y_info, CW * 0.5, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Numero :  {data.get('numero', '')}")

        # Séparateur pointillé
        y_dot_h = y_info + row_h + mm(1.5)
        pen_dot = QPen(C_BLACK, mm(0.28))
        pen_dot.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen_dot)
        painter.drawLine(int(X), int(y_dot_h), int(X + CW), int(y_dot_h))

        # ── CORPS : GRILLE LIBELLÉS + 3 COLONNES DE VALEURS ──────────────────
        #
        #  | LIBELLÉS (30%) | SCOLARITE (23%) | TRANSPORT (23%) | CANTINE (24%) |
        #  |─────────────────────────────────────────────────────────────────────|
        #  | Montant dû :   |   120 000 F     |   110 000 F     |  100 000 F    |
        #  | Montant reçu : |    20 000 F     |    30 000 F     |       0 F     |
        #  | Reste à verser:|   100 000 F     |    80 000 F     |  100 000 F    |

        lbl_w = CW * 0.28           # colonne libellés
        val_w = (CW - lbl_w) / 3   # largeur de chaque colonne rubrique (égales)

        x_lbl   = X
        x_scol  = X + lbl_w
        x_trans = x_scol + val_w
        x_cant  = x_trans + val_w

        y_body_top   = y_dot_h
        y_footer_top = Y + CH - mm(37)

        # Ligne corps / pied de page
        painter.setPen(QPen(C_BLACK, mm(0.22)))
        painter.drawLine(int(X), int(y_footer_top), int(X + CW), int(y_footer_top))

        # Séparateur vertical gauche (libellés / valeurs) — trait continu fin
        painter.setPen(QPen(C_BORDER, mm(0.25)))
        painter.drawLine(int(x_scol), int(y_dot_h), int(x_scol), int(y_footer_top))

        # Séparateurs verticaux entre colonnes de valeurs — pointillés
        for sep_x in [x_trans, x_cant]:
            pen_v = QPen(C_BORDER, mm(0.25))
            pen_v.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen_v)
            painter.drawLine(int(sep_x), int(y_dot_h), int(sep_x), int(y_footer_top))

        # ── Titres des rubriques ──────────────────────────────────────────────
        TITLE_H = mm(13)
        sections_meta = [
            ("SCOLARITE", x_scol,  "scol_active"),
            ("TRANSPORT", x_trans, "trans_active"),
            ("CANTINE",   x_cant,  "cant_active"),
        ]
        for title, tx, act_key in sections_meta:
            active = data.get(act_key, False)
            painter.setFont(_font(11, bold=True))
            painter.setPen(QPen(C_BLACK if active else C_MUTED))
            painter.drawText(
                QRectF(tx + mm(1), y_body_top + mm(2), val_w - mm(2), TITLE_H - mm(2)),
                Qt.AlignmentFlag.AlignCenter,
                title,
            )
            # Filet bleu sous le titre (si actif)
            if active:
                painter.fillRect(
                    QRectF(tx + mm(4), y_body_top + TITLE_H - mm(0.8), val_w - mm(8), mm(0.8)),
                    C_BLUE,
                )

        # ── Lignes de données ─────────────────────────────────────────────────
        data_rows = [
            ("Montant dû :",      "scol_due",   "trans_due",   "cant_due",   False),
            ("Montant reçu :",    "scol_recu",  "trans_recu",  "cant_recu",  False),
            ("Reste à verser :",  "scol_reste", "trans_reste", "cant_reste", True),
        ]
        val_cols = [
            (x_scol,  "scol_active"),
            (x_trans, "trans_active"),
            (x_cant,  "cant_active"),
        ]
        d_row_h = mm(11)
        y_row = y_body_top + TITLE_H + mm(1)

        for label, sk, tk, ck, is_reste in data_rows:
            row_vkeys = (sk, tk, ck)
            # Libellé — une seule fois à gauche
            painter.setFont(_font(9, bold=is_reste))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(
                QRectF(x_lbl + mm(3), y_row, lbl_w - mm(4), d_row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )

            # Valeurs pour chaque rubrique
            for col_idx, (tx, act_key) in enumerate(val_cols):
                active = data.get(act_key, False)
                vkey = row_vkeys[col_idx]
                val = data.get(vkey, 0)

                if not active:
                    col = C_MUTED
                    text = "—"
                elif is_reste:
                    col = C_GREEN if float(val) <= 0.0 else C_ORANGE
                    text = _fmt(val)
                else:
                    col = C_BLACK
                    text = _fmt(val)

                painter.setFont(_font(9, bold=True))
                painter.setPen(QPen(col))
                painter.drawText(
                    QRectF(tx + mm(2), y_row, val_w - mm(4), d_row_h),
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                    text,
                )

            # Filet de séparation entre lignes de données
            if not is_reste:
                painter.setPen(QPen(QColor(220, 220, 220), mm(0.15)))
                painter.drawLine(
                    int(X + mm(2)), int(y_row + d_row_h - mm(0.5)),
                    int(X + CW - mm(2)), int(y_row + d_row_h - mm(0.5)),
                )

            y_row += d_row_h

        # ── Filigranes SOLDE (par colonne de valeur) ──────────────────────────
        for (tx, act_key, reste_key) in [
            (x_scol,  "scol_active",  "scol_reste"),
            (x_trans, "trans_active", "trans_reste"),
            (x_cant,  "cant_active",  "cant_reste"),
        ]:
            if data.get(act_key, False) and float(data.get(reste_key, 1)) <= 0.0:
                painter.save()
                painter.translate(tx + val_w / 2, (y_body_top + TITLE_H + y_footer_top) / 2)
                painter.rotate(-28)
                painter.setFont(_font(20, bold=True))
                painter.setPen(QPen(QColor(22, 163, 74, 55), 1))
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance("SOLDE")
                th = fm.height()
                painter.drawText(int(-tw / 2), int(th / 4), "SOLDE")
                painter.restore()

        # ── PIED DE PAGE ─────────────────────────────────────────────────────
        nb_h = mm(13)
        nb_y = y_footer_top + mm(2)

        nb_text = (
            "NB : Tout paiement effectué ne sera pas remboursé, si les paiements ne sont pas "
            "effectués selon l'échéance fixée, l'enfant peut être retourné à la maison.   "
            "Si l'enfant cesse de prendre le car ou arrête de manger à la cantine, merci "
            "de mentionner par écrit à la comptabilité."
        )

        painter.setFont(_font(6))
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(X + mm(2), nb_y, CW - mm(4), nb_h),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
            nb_text,
        )

        # Signature unique centrée
        cx = X + CW / 2
        y_sig = nb_y + nb_h + mm(4)

        painter.setPen(QPen(C_BLACK, mm(0.28)))
        painter.drawLine(int(cx - mm(30)), int(y_sig), int(cx + mm(30)), int(y_sig))

        f_sig = _font(9, bold=True)
        f_sig.setUnderline(True)
        painter.setFont(f_sig)
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(cx - mm(32), y_sig + mm(1.5), mm(64), mm(7)),
            Qt.AlignmentFlag.AlignCenter,
            "Signature et cachet",
        )

        # ── BANDEROLE BAS ─────────────────────────────────────────────────────
        y_bot = Y + CH - mm(9)
        painter.setPen(QPen(C_BLACK, mm(0.28)))
        painter.drawLine(int(X + mm(1.5)), int(y_bot), int(X + CW - mm(1.5)), int(y_bot))

        painter.setFont(_font(9, bold=True))
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(X, y_bot + mm(0.8), CW, mm(8)),
            Qt.AlignmentFlag.AlignCenter,
            "APPORTER CE RECU AU PROCHAIN VERSEMENT",
        )

        painter.end()
