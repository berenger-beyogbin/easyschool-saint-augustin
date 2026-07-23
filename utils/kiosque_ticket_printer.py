from html import escape

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from app.session import AppSession
from utils.print_helpers import get_etablissement_print_info


class KiosqueTicketPrinter:
    @staticmethod
    def print_ticket(parent, lignes):
        if not lignes:
            return
        etab = get_etablissement_print_info(parent)
        if etab is None:
            return
        premier = lignes[0]
        total = sum(float(l.Prix_vente or 0) * int(l.QuantiteSort or 0) for l in lignes)
        remise = sum(float(l.RemiseMontant or 0) for l in lignes)
        rows = "".join(
            f"<tr><td>{escape(l.article.Libelle if l.article else 'Article')}</td>"
            f"<td align='right'>{l.QuantiteSort}</td>"
            f"<td align='right'>{float(l.Prix_vente or 0):,.0f}</td>"
            f"<td align='right'>{float(l.Prix_vente or 0) * l.QuantiteSort:,.0f}</td></tr>"
            for l in lignes
        )
        annulation = ""
        if (premier.Statut or "VALIDE") == "ANNULE":
            annulation = f"<p style='color:#b91c1c'><b>TICKET ANNULÉ</b><br>{escape(premier.MotifAnnulation or '')}</p>"
        html = f"""
        <div style='font-family:Arial;font-size:10pt'>
          <h2 style='text-align:center'>{escape(etab.nom)}</h2>
          <p style='text-align:center'>{escape(etab.telephone or '')}</p>
          <h3 style='text-align:center'>TICKET KIOSQUE</h3>
          <p><b>Référence :</b> {escape(premier.ReferenceVente or '')}<br>
          <b>Date :</b> {premier.DateSort.strftime('%d/%m/%Y')} {str(premier.HeureSortie)[:8]}<br>
          <b>Caissier :</b> {escape(premier.Login or '')}</p>
          <table width='100%' cellspacing='0' cellpadding='4' border='1'>
            <tr><th>Article</th><th>Qté</th><th>P.U.</th><th>Total</th></tr>{rows}
          </table>
          <p style='text-align:right'><b>Remise : {remise:,.0f} F CFA</b><br>
          <span style='font-size:14pt'><b>TOTAL : {total:,.0f} F CFA</b></span></p>
          {annulation}
          <p style='text-align:center'>Merci pour votre achat.</p>
        </div>"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preferred = AppSession.get_current_user_imprimante()
        if preferred:
            printer.setPrinterName(preferred)
        document = QTextDocument()
        document.setHtml(html)
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle("Aperçu — Ticket kiosque")
        preview.resize(700, 850)
        preview.paintRequested.connect(lambda p: document.print_(p))
        preview.exec()
