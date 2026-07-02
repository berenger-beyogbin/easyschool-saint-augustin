from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QPageSize, QPageLayout
from PySide6.QtCore import Qt, QRectF

from app.config import Config

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


# ── Montant en lettres (français, entiers uniquement) ─────────────────────────
_UNITES = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
           "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
           "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
             "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]


def _deux_chiffres_en_lettres(n: int) -> str:
    if n < 20:
        return _UNITES[n]
    dix, unite = divmod(n, 10)
    if dix in (7, 9):
        base, reste = _DIZAINES[dix - 1], 10 + unite
        if unite == 1 and dix == 7:
            return f"{base} et {_UNITES[reste]}"
        return f"{base}-{_UNITES[reste]}"
    if unite == 0:
        return f"{_DIZAINES[dix]}s" if dix == 8 else _DIZAINES[dix]
    if unite == 1 and dix != 8:
        return f"{_DIZAINES[dix]} et un"
    return f"{_DIZAINES[dix]}-{_UNITES[unite]}"


def _trois_chiffres_en_lettres(n: int) -> str:
    centaine, reste = divmod(n, 100)
    parts = []
    if centaine > 0:
        parts.append("cent" if centaine == 1 else f"{_UNITES[centaine]} cent" + ("s" if reste == 0 else ""))
    if reste > 0:
        parts.append(_deux_chiffres_en_lettres(reste))
    return " ".join(parts) if parts else "zéro"


def _montant_en_lettres(v) -> str:
    """Convertit un montant FCFA entier en toutes lettres (français)."""
    try:
        n = int(float(v))
    except Exception:
        return ""
    if n == 0:
        return "Zéro franc CFA"

    reste = abs(n)
    milliards, reste = divmod(reste, 1_000_000_000)
    millions, reste = divmod(reste, 1_000_000)
    milliers, unites = divmod(reste, 1000)

    parts = []
    if milliards > 0:
        parts.append(f"{_trois_chiffres_en_lettres(milliards)} milliard" + ("s" if milliards > 1 else ""))
    if millions > 0:
        parts.append(f"{_trois_chiffres_en_lettres(millions)} million" + ("s" if millions > 1 else ""))
    if milliers > 0:
        parts.append("mille" if milliers == 1 else f"{_trois_chiffres_en_lettres(milliers)} mille")
    if unites > 0 or not parts:
        parts.append(_trois_chiffres_en_lettres(unites))

    texte = " ".join(parts)
    texte = f"moins {texte}" if n < 0 else texte
    unite_franc = "franc" if abs(n) == 1 else "francs"
    return f"{texte[0].upper()}{texte[1:]} {unite_franc} CFA"


def _font(size_pt: float, bold: bool = False) -> QFont:
    f = QFont("Arial", size_pt)
    f.setBold(bold)
    return f


def _draw_centered_fit_text(painter: QPainter, rect: QRectF, text: str,
                             base_size: float, bold: bool = True, min_size: float = 6.0) -> None:
    """Dessine `text` centré dans `rect` sans jamais dépasser sa largeur.
    Réduit progressivement la taille de police jusqu'à `min_size` ; si le texte
    est encore trop large, il est réparti sur deux lignes centrées."""
    if not text:
        return

    size = base_size
    font = _font(size, bold)
    painter.setFont(font)
    fm = painter.fontMetrics()
    while fm.horizontalAdvance(text) > rect.width() and size > min_size:
        size -= 0.5
        font = _font(size, bold)
        painter.setFont(font)
        fm = painter.fontMetrics()

    if fm.horizontalAdvance(text) <= rect.width():
        painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, text)
        return

    # Toujours trop large à la taille minimale : répartir sur deux lignes
    words = text.split(" ")
    line1, line2 = text, ""
    best_w = None
    for i in range(1, len(words)):
        candidate1 = " ".join(words[:i])
        candidate2 = " ".join(words[i:])
        w = max(fm.horizontalAdvance(candidate1), fm.horizontalAdvance(candidate2))
        if best_w is None or w < best_w:
            best_w, line1, line2 = w, candidate1, candidate2

    half_h = rect.height() / 2
    painter.drawText(QRectF(rect.x(), rect.y(), rect.width(), half_h),
                      Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, line1)
    painter.drawText(QRectF(rect.x(), rect.y() + half_h, rect.width(), half_h),
                      Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, line2)


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

        _draw_centered_fit_text(
            painter,
            QRectF(X + mm(2), Y + mm(8), CW - mm(4), mm(12)),
            hdr_line2,
            base_size=20, bold=True, min_size=11,
        )

        _draw_centered_fit_text(
            painter,
            QRectF(X + mm(2), Y + mm(19), CW - mm(4), mm(6)),
            hdr_line3,
            base_size=8, bold=True, min_size=5.5,
        )

        # Ligne fine sous l'en-tête, avec le libellé du document au centre
        y_sep1 = Y + mm(26)
        label_recu = "REÇU DE PAIEMENT"
        painter.setFont(_font(9, bold=True))
        label_w = painter.fontMetrics().horizontalAdvance(label_recu) + mm(4)
        mid_x = X + CW / 2

        painter.setPen(QPen(C_BLACK, mm(0.22)))
        painter.drawLine(int(X + mm(1.5)), int(y_sep1), int(mid_x - label_w / 2), int(y_sep1))
        painter.drawLine(int(mid_x + label_w / 2), int(y_sep1), int(X + CW - mm(1.5)), int(y_sep1))
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(mid_x - label_w / 2, y_sep1 - mm(3), label_w, mm(6)),
            Qt.AlignmentFlag.AlignCenter,
            label_recu,
        )

        # ── INFOS ÉLÈVE ───────────────────────────────────────────────────────
        y_info = y_sep1 + mm(2)
        row_h = mm(5)
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
                         f"Numéro :  {data.get('numero', '')}")

        # Motif / Mode de paiement / Titulaire — enrichissement CJGA
        # (valeurs UI temporaires, non persistées en base à ce stade)
        y_info += row_h
        painter.setFont(_font(8, bold=True))
        painter.drawText(QRectF(X + mm(3), y_info, CW * 0.36, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Motif :  {data.get('motif', 'Scolarité')}")
        painter.drawText(QRectF(X + CW * 0.37, y_info, CW * 0.34, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Mode :  {data.get('mode_paiement', 'Espèce')}")
        painter.drawText(QRectF(X + CW * 0.70, y_info, CW * 0.30, row_h),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         f"Titulaire :  {data.get('titulaire', 'Non précisé')}")

        # Séparateur pointillé
        y_dot_h = y_info + row_h + mm(1.5)
        pen_dot = QPen(C_BLACK, mm(0.28))
        pen_dot.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen_dot)
        painter.drawLine(int(X), int(y_dot_h), int(X + CW), int(y_dot_h))

        # ── CORPS : GRILLE LIBELLÉS + COLONNES DES RUBRIQUES ACTIVES ─────────
        #
        # Seules les rubriques actives sont dessinées (Scolarité toujours
        # affichée ; Transport/Cantine uniquement si actives pour cet élève).
        # Une rubrique désactivée n'a pas de colonne du tout (pas de "—" grisé).
        sections_def = [
            ("SCOLARITE", "scol_active",  "scol_due",  "scol_recu",  "scol_reste",  True),
            ("TRANSPORT", "trans_active", "trans_due", "trans_recu", "trans_reste", False),
            ("CANTINE",   "cant_active",  "cant_due",  "cant_recu",  "cant_reste",  False),
        ]
        sections = [s for s in sections_def if s[5] or data.get(s[1], False)]

        lbl_w = CW * 0.28                       # colonne libellés
        val_w = (CW - lbl_w) / len(sections)    # largeur de chaque colonne rubrique active
        x_lbl = X
        x_cols = [x_lbl + lbl_w + i * val_w for i in range(len(sections))]

        y_body_top   = y_dot_h
        y_footer_top = Y + CH - mm(37)

        # Ligne corps / pied de page
        painter.setPen(QPen(C_BLACK, mm(0.22)))
        painter.drawLine(int(X), int(y_footer_top), int(X + CW), int(y_footer_top))

        # Séparateur vertical gauche (libellés / valeurs) — trait continu fin
        painter.setPen(QPen(C_BORDER, mm(0.25)))
        painter.drawLine(int(x_cols[0]), int(y_dot_h), int(x_cols[0]), int(y_footer_top))

        # Séparateurs verticaux entre colonnes de valeurs — pointillés
        for sep_x in x_cols[1:]:
            pen_v = QPen(C_BORDER, mm(0.25))
            pen_v.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen_v)
            painter.drawLine(int(sep_x), int(y_dot_h), int(sep_x), int(y_footer_top))

        # ── Titres des rubriques ──────────────────────────────────────────────
        TITLE_H = mm(11)
        for section, tx in zip(sections, x_cols):
            title, act_key = section[0], section[1]
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
        # (label, index du champ dans section_def : 2=due, 3=recu, 4=reste)
        row_defs = [
            ("Montant dû :",      2, False),
            ("Montant reçu :",    3, False),
            ("Reste à verser :",  4, True),
        ]
        d_row_h = mm(11)
        y_row = y_body_top + TITLE_H + mm(1)

        for label, field_idx, is_reste in row_defs:
            # Libellé — une seule fois à gauche
            painter.setFont(_font(9, bold=is_reste))
            painter.setPen(QPen(C_BLACK))
            painter.drawText(
                QRectF(x_lbl + mm(3), y_row, lbl_w - mm(4), d_row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )

            # Valeurs pour chaque rubrique active
            for section, tx in zip(sections, x_cols):
                act_key, vkey = section[1], section[field_idx]
                active = data.get(act_key, False)
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
        for section, tx in zip(sections, x_cols):
            act_key, reste_key = section[1], section[4]
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

        # Montant total reçu + montant en lettres — enrichissement CJGA
        total_recu = data.get("total_recu")
        if total_recu is None:
            total_recu = (
                float(data.get("scol_recu", 0) or 0) +
                float(data.get("trans_recu", 0) or 0) +
                float(data.get("cant_recu", 0) or 0)
            )
        total_h = mm(4)
        total_line = f"Montant total reçu :  {_fmt(total_recu)}  —  {_montant_en_lettres(total_recu)}"
        painter.setFont(_font(8, bold=True))
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(X + mm(2), nb_y, CW - mm(4), total_h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
            total_line,
        )

        clause_services = " ou ".join(
            s for s, actif in (("du transport", Config.ENABLE_TRANSPORT),
                                ("de la cantine", Config.ENABLE_CANTINE)) if actif
        )
        nb_text = "NB : Tout paiement effectué n'est pas remboursable. Le non-respect de l'échéance peut entraîner le renvoi de l'enfant."
        if clause_services:
            nb_text += f" Prévenir la comptabilité par écrit en cas d'arrêt {clause_services}."

        painter.setFont(_font(5.5))
        painter.setPen(QPen(C_BLACK))
        painter.drawText(
            QRectF(X + mm(2), nb_y + total_h, CW - mm(4), nb_h - total_h),
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
