from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import func

from app.database import get_session
from app.session import AppSession
from models.article import Article
from models.classe import TClasse
from models.inscription import TInscription
from models.montant_cantine import MontantCantine
from models.montant_scol import MontantScol
from models.montant_transport import MontantTransport
from models.sortie_fin import SortieFin
from models.stock_cour import StockCour
from models.stock_sortie import StockSortie
from models.versement_scol import VersementScol
from services.dashboard_service import DashboardService


class DashboardV2Service:
    """Requetes de pilotage de la V2, sans modifier le tableau de bord historique."""

    @staticmethod
    def _period_start(period: str) -> date | None:
        today = date.today()
        if period == "today":
            return today
        if period == "month":
            return today.replace(day=1)
        return None

    @staticmethod
    def _rate(paid: float, due: float) -> int:
        return min(100, round((paid / due) * 100)) if due > 0 else 0

    @staticmethod
    def get_pilotage(period: str = "year") -> dict:
        id_annee = AppSession.get_active_annee_id()
        empty = {
            "inscrits": 0, "nouveaux": 0, "classes": 0,
            "scolarite": {"paid": 0, "due": 0, "remaining": 0, "rate": 0},
            "cantine": {"paid": 0, "due": 0, "remaining": 0, "rate": 0},
            "transport": {"paid": 0, "due": 0, "remaining": 0, "rate": 0},
            "autres": 0, "kiosque": 0, "recettes": 0, "depenses": 0,
            "solde": 0, "reductions": 0, "operations": 0,
            "stock_value": 0, "ruptures": 0,
        }
        if not id_annee:
            return empty

        start = DashboardV2Service._period_start(period)
        session = get_session()
        try:
            inscriptions = session.query(TInscription).filter(
                TInscription.IDTAnneeScolaire == id_annee
            ).all()
            tarifs_s = {m.IDNiveau: m for m in session.query(MontantScol).filter_by(IDTAnneeScolaire=id_annee)}
            tarifs_c = {m.IDNiveau: float(m.Montant or 0) for m in session.query(MontantCantine).filter_by(IDTAnneeScolaire=id_annee)}
            tarifs_t = {m.IDNiveau: float(m.Montant or 0) for m in session.query(MontantTransport).filter_by(IDTAnneeScolaire=id_annee)}

            family_order = defaultdict(list)
            for ins in sorted(inscriptions, key=lambda x: x.IDTInscription):
                family_order[ins.IDFamille].append(ins.IDEleve)
            family_rank = {
                student: (index + 1, len(students))
                for students in family_order.values()
                for index, student in enumerate(students)
            }

            due_s = due_c = due_t = 0.0
            for ins in inscriptions:
                if ins.Scolarite and ins.IDNiveau in tarifs_s:
                    tarif = tarifs_s[ins.IDNiveau]
                    if ins.famille and ins.famille.EnsCatPrimaire:
                        amount = float(tarif.MontantEnsPri or 0)
                    elif ins.famille and ins.famille.EnsCatSecondaire:
                        amount = float(tarif.MontantEnsSecondaire or 0)
                    else:
                        amount = float(tarif.Montant or 0)
                    if ins.famille and ins.famille.EbrieAbobote:
                        amount = max(0, amount - 10000)
                    if ins.Nouveau:
                        amount += 10000
                    rank, count = family_rank.get(ins.IDEleve, (1, 1))
                    if count >= 3 and rank >= 3:
                        amount = max(0, amount - 10000)
                    due_s += amount
                if ins.Cantine:
                    due_c += tarifs_c.get(ins.IDNiveau, 0)
                if ins.Transport:
                    due_t += tarifs_t.get(ins.IDNiveau, 0)

            all_payments = session.query(VersementScol).filter(
                VersementScol.IDTAnneeScolaire == id_annee
            ).all()
            payment_query = session.query(VersementScol).filter(
                VersementScol.IDTAnneeScolaire == id_annee
            )
            expense_query = session.query(SortieFin).filter(
                SortieFin.IDAnSco == id_annee, SortieFin.DebitCredit == "Debit"
            )
            sale_query = session.query(StockSortie).filter(
                StockSortie.IDTAnneeScolaire == id_annee, StockSortie.Statut == "VALIDE"
            )
            if start:
                payment_query = payment_query.filter(VersementScol.DateVers >= start)
                expense_query = expense_query.filter(SortieFin.DateSortie >= start)
                sale_query = sale_query.filter(StockSortie.DateSort >= start)

            payments = payment_query.all()
            paid_s = sum(float(v.MontantVersSco or 0) for v in all_payments if not v.Reduction)
            paid_c = sum(float(v.MontantCantine or 0) for v in all_payments if not v.Reduction)
            paid_t = sum(float(v.MontantVersTrans or 0) for v in all_payments if not v.Reduction)
            recovery_reductions = sum(float(v.MontantVersSco or 0) for v in all_payments if v.Reduction)
            period_s = sum(float(v.MontantVersSco or 0) for v in payments if not v.Reduction)
            period_c = sum(float(v.MontantCantine or 0) for v in payments if not v.Reduction)
            period_t = sum(float(v.MontantVersTrans or 0) for v in payments if not v.Reduction)
            paid_o = sum(float(v.MontantVersAutres or 0) for v in payments if not v.Reduction)
            reductions = sum(float(v.MontantVersSco or 0) for v in payments if v.Reduction)
            sales = sale_query.all()
            kiosk = sum(float(v.QuantiteSort or 0) * float(v.Prix_vente or 0) for v in sales)
            expenses = sum(float(v.Montant or 0) for v in expense_query.all())
            receipts = period_s + period_c + period_t + paid_o + kiosk

            stocks = session.query(StockCour, Article).join(Article).all()
            stock_value = sum(float(sc.QuantiteCour or 0) * float(a.PU or 0) for sc, a in stocks)
            ruptures = sum(1 for sc, _ in stocks if (sc.QuantiteCour or 0) == 0)

            def recovery(paid, due, reduction=0):
                covered = paid + reduction
                return {
                    "paid": paid, "due": due,
                    "remaining": max(0, due - covered),
                    "rate": DashboardV2Service._rate(covered, due),
                }

            return {
                "inscrits": len(inscriptions),
                "nouveaux": sum(1 for i in inscriptions if i.Nouveau),
                "classes": session.query(TClasse).filter_by(IDAnneeScolaire=id_annee).count(),
                "scolarite": recovery(paid_s, due_s, recovery_reductions),
                "cantine": recovery(paid_c, due_c),
                "transport": recovery(paid_t, due_t),
                "autres": paid_o, "kiosque": kiosk,
                "recettes": receipts, "depenses": expenses,
                "solde": receipts - expenses, "reductions": reductions,
                "operations": len(payments) + len(sales),
                "stock_value": stock_value, "ruptures": ruptures,
            }
        except Exception as exc:
            print(f"Erreur get_pilotage Dashboard V2 : {exc}")
            return empty
        finally:
            session.close()

    @staticmethod
    def get_monthly_trend(months: int = 6) -> list[dict]:
        id_annee = AppSession.get_active_annee_id()
        if not id_annee:
            return []
        session = get_session()
        try:
            payments = session.query(VersementScol).filter(
                VersementScol.IDTAnneeScolaire == id_annee,
                VersementScol.Reduction == False,
            ).all()
            sales = session.query(StockSortie).filter(
                StockSortie.IDTAnneeScolaire == id_annee,
                StockSortie.Statut == "VALIDE",
            ).all()
            totals = defaultdict(float)
            for v in payments:
                if v.DateVers:
                    totals[v.DateVers.strftime("%Y-%m")] += sum(float(x or 0) for x in (
                        v.MontantVersSco, v.MontantCantine, v.MontantVersTrans, v.MontantVersAutres
                    ))
            for v in sales:
                if v.DateSort:
                    totals[v.DateSort.strftime("%Y-%m")] += float(v.QuantiteSort or 0) * float(v.Prix_vente or 0)
            return [{"month": key, "amount": totals[key]} for key in sorted(totals)[-months:]]
        finally:
            session.close()

    @staticmethod
    def get_alerts() -> list[dict]:
        alerts = []
        for item in DashboardService.get_impayes_scolarite(5):
            alerts.append({"level": "danger", "title": "Impayé scolarité", "detail": f"{item['eleve']} · reste {item['reste']}", "target": "scolarite"})
        for item in DashboardService.get_stock_alerts(5):
            level = "danger" if item["stock"] == 0 else "warning"
            alerts.append({"level": level, "title": "Rupture de stock" if level == "danger" else "Stock faible", "detail": f"{item['article']} · {item['stock']} unité(s)", "target": "kiosque"})
        for item in DashboardService.get_classes_capacity_alerts(5):
            alerts.append({"level": "warning", "title": "Capacité de classe", "detail": f"{item['classe']} · {item['effectif']}/{item['capacite']} ({item['pct']} %)", "target": "scolarite"})
        return alerts
