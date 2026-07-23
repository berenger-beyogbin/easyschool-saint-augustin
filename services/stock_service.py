import datetime
import uuid
from typing import List, Tuple, Optional, Mapping
from decimal import Decimal
from sqlalchemy.orm import joinedload
from models.article import Article
from models.stock_cour import StockCour
from models.stock_entree import StockEntree
from models.stock_sortie import StockSortie
from models.kit_composant import KitComposant
from models.kit_assemblage import KitAssemblage
from models.annee_scolaire import TAnneeScolaire
from app.database import get_session
from app.session import AppSession

class StockService:
    @staticmethod
    def _require_permission(code: str) -> Tuple[bool, str]:
        return AppSession.require_permission(code)

    @staticmethod
    def _current_login() -> str:
        return AppSession.get_logged_in_username() or "system"

    @staticmethod
    def _validate_open_school_year(session, id_annee: int) -> Tuple[bool, str]:
        """Bloque tout mouvement de stock si l'année est absente ou clôturée."""
        if not id_annee:
            return False, "Aucune annee scolaire configuree active."

        annee = session.get(TAnneeScolaire, id_annee)
        if not annee:
            return False, "Annee scolaire introuvable."
        if annee.Cloturer:
            return False, "Impossible d'enregistrer un mouvement de stock : l'annee scolaire est cloturee."
        return True, ""

    @staticmethod
    def get_stock_courant() -> List[StockCour]:
        """Recupere la liste complete des stocks courants."""
        session = get_session()
        try:
            return session.query(StockCour).all()
        except Exception as e:
            print(f"Erreur get_stock_courant : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_stock_by_article(id_art: int) -> Optional[StockCour]:
        """Recupere le stock courant pour un article specifique."""
        session = get_session()
        try:
            return session.query(StockCour).filter_by(IDTArticle=id_art).first()
        except Exception as e:
            print(f"Erreur get_stock_by_article : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def add_stock(id_art: int, qte: int, id_annee: int, login: str, date_ent=None) -> Tuple[bool, str]:
        """Approvisionne un article ou assemble un kit en consommant ses composants."""
        if qte <= 0:
            return False, "La quantite de reapprovisionnement doit etre strictement positive."
        allowed, msg = StockService._require_permission("KIOSQUE_STOCKS")
        if not allowed:
            return False, msg

        session = get_session()
        try:
            ok, msg = StockService._validate_open_school_year(session, id_annee)
            if not ok:
                return False, msg

            article = session.get(Article, id_art)
            if not article:
                return False, "Article introuvable."
            composants = []
            if article.KIT:
                composants = session.query(KitComposant).options(
                    joinedload(KitComposant.article)
                ).filter_by(IDKit=id_art).order_by(KitComposant.IDArticle).all()
                if not composants:
                    return False, "Ce kit ne possède aucune composition exploitable."

            # Ordre stable de verrouillage pour éviter survente et interblocages.
            ids_a_verrouiller = sorted({id_art, *(c.IDArticle for c in composants)})
            stocks = session.query(StockCour).filter(
                StockCour.IDTArticle.in_(ids_a_verrouiller)
            ).order_by(StockCour.IDTArticle).with_for_update().all()
            stocks_par_article = {stock.IDTArticle: stock for stock in stocks}
            sc = stocks_par_article.get(id_art)
            if not sc:
                sc = StockCour(IDTArticle=id_art, QuantiteCour=0)
                session.add(sc)

            insuffisants = []
            for composant in composants:
                requis = composant.Quantite * qte
                stock_composant = stocks_par_article.get(composant.IDArticle)
                disponible = stock_composant.QuantiteCour if stock_composant else 0
                if disponible < requis:
                    nom = composant.article.Libelle if composant.article else str(composant.IDArticle)
                    insuffisants.append(f"{nom}: requis {requis}, disponible {disponible}")
            if insuffisants:
                return False, "Assemblage impossible — stock insuffisant : " + "; ".join(insuffisants)

            for composant in composants:
                stocks_par_article[composant.IDArticle].QuantiteCour -= composant.Quantite * qte
            sc.QuantiteCour += qte

            # Creation entree historic
            entree = StockEntree(
                IDTAnneeScolaire=id_annee,
                IDTArticle=id_art,
                DateEnt=date_ent or datetime.date.today(),
                QuantiteEnt=qte,
                Login=StockService._current_login()
            )
            session.add(entree)
            session.flush()
            for composant in composants:
                session.add(KitAssemblage(
                    IDStockEnt=entree.IDStockEnt,
                    IDKit=id_art,
                    IDArticle=composant.IDArticle,
                    DateAssemblage=entree.DateEnt,
                    QuantiteKits=qte,
                    QuantiteConsommee=composant.Quantite * qte,
                    Login=StockService._current_login(),
                ))
            session.commit()
            if composants:
                return True, f"Assemblage de {qte} kit(s) effectué ; les composants ont été déstockés."
            return True, f"Approvisionnement de {qte} unite(s) effectue avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement de l'approvisionnement : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_capacite_assemblage(id_art: int) -> Optional[dict]:
        """Retourne la capacité maximale d'assemblage et le détail des composants."""
        session = get_session()
        try:
            article = session.get(Article, id_art)
            if not article or not article.KIT:
                return None
            composants = session.query(KitComposant).options(
                joinedload(KitComposant.article)
            ).filter_by(IDKit=id_art).all()
            if not composants:
                return {"maximum": 0, "details": []}
            stocks = {
                s.IDTArticle: s.QuantiteCour for s in session.query(StockCour).filter(
                    StockCour.IDTArticle.in_([c.IDArticle for c in composants])
                ).all()
            }
            details = []
            capacites = []
            for composant in composants:
                disponible = stocks.get(composant.IDArticle, 0)
                capacites.append(disponible // composant.Quantite)
                details.append({
                    "article": composant.article.Libelle if composant.article else str(composant.IDArticle),
                    "par_kit": composant.Quantite,
                    "stock": disponible,
                })
            return {"maximum": min(capacites), "details": details}
        finally:
            session.close()

    @staticmethod
    def remove_stock(id_art: int, qte: int, id_annee: int, prix_vente: float, login: str) -> Tuple[bool, str]:
        """
        Diminue le stock courant d'un article suite a une vente et enregistre la sortie.
        Renvoie (False, Message) si stock insuffisant.
        """
        if qte <= 0:
            return False, "La quantite vendue doit etre strictement positive."
        try:
            prix = Decimal(str(prix_vente))
        except Exception:
            return False, "Le prix de vente est invalide."
        if not prix.is_finite() or prix < 0:
            return False, "Le prix de vente ne doit pas etre negatif."
        allowed, msg = StockService._require_permission("KIOSQUE_VENTES")
        if not allowed:
            return False, msg
            
        session = get_session()
        try:
            ok, msg = StockService._validate_open_school_year(session, id_annee)
            if not ok:
                return False, msg

            article = session.get(Article, id_art)
            if not article:
                return False, "Article introuvable."
            if prix != article.PU:
                return False, "Le prix de vente ne correspond plus au prix catalogue."
            sc = session.query(StockCour).filter_by(IDTArticle=id_art).with_for_update().first()
            if not sc or sc.QuantiteCour < qte:
                stock_dispo = sc.QuantiteCour if sc else 0
                return False, f"Stock insuffisant. Quantite disponible : {stock_dispo}."

            sc.QuantiteCour -= qte

            # Creation sortie
            now_time = datetime.datetime.now().time()
            sortie = StockSortie(
                IDTAnneeScolaire=id_annee,
                IDTArticle=id_art,
                DateSort=datetime.date.today(),
                QuantiteSort=qte,
                Prix_vente=prix,
                PrixCatalogue=article.PU,
                RemiseMontant=Decimal("0"),
                Statut="VALIDE",
                HeureSortie=now_time,
                Login=StockService._current_login(),
                ReferenceVente=str(uuid.uuid4())
            )
            session.add(sortie)
            session.commit()
            return True, f"Vente de {qte} unite(s) enregistree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la soustraction de stock : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def enregistrer_panier(panier: Mapping[int, Mapping[str, object]], id_annee: int) -> Tuple[bool, str]:
        """Valide toutes les lignes sous verrous et dans une transaction unique."""
        if not panier:
            return False, "Le panier est vide."
        allowed, msg = StockService._require_permission("KIOSQUE_VENTES")
        if not allowed:
            return False, msg
        session = get_session()
        try:
            ok, msg = StockService._validate_open_school_year(session, id_annee)
            if not ok:
                return False, msg
            ids = sorted(panier)
            stocks = session.query(StockCour).filter(StockCour.IDTArticle.in_(ids)).order_by(
                StockCour.IDTArticle
            ).with_for_update().all()
            par_article = {stock.IDTArticle: stock for stock in stocks}
            articles = {row.IDTArticle: row for row in session.query(Article).filter(Article.IDTArticle.in_(ids)).all()}
            lignes, erreurs = [], []
            for id_art in ids:
                info = panier[id_art]
                try:
                    qte = int(info["qte"])
                    prix = Decimal(str(info["pu"]))
                except (KeyError, TypeError, ValueError, ArithmeticError):
                    erreurs.append(f"article {id_art} invalide")
                    continue
                stock = par_article.get(id_art)
                disponible = stock.QuantiteCour if stock else 0
                article = articles.get(id_art)
                motif_remise = str(info.get("motif_remise") or "").strip()
                if not article:
                    erreurs.append(f"article {id_art} introuvable")
                elif qte <= 0 or not prix.is_finite() or prix < 0:
                    erreurs.append(f"article {id_art}: quantite ou prix invalide")
                elif prix > article.PU:
                    erreurs.append(f"article {id_art}: prix superieur au catalogue")
                elif prix != article.PU and not AppSession.has_permission("KIOSQUE_REMISES"):
                    erreurs.append(f"article {id_art}: droit KIOSQUE_REMISES requis")
                elif prix != article.PU and not motif_remise:
                    erreurs.append(f"article {id_art}: motif de remise obligatoire")
                elif qte > disponible:
                    erreurs.append(f"article {id_art}: demande {qte}, disponible {disponible}")
                else:
                    lignes.append((stock, qte, prix, article.PU, motif_remise))
            if erreurs:
                return False, "Vente annulee : " + "; ".join(erreurs)
            maintenant = datetime.datetime.now()
            login = StockService._current_login()
            reference = str(uuid.uuid4())
            for stock, qte, prix, prix_catalogue, motif_remise in lignes:
                stock.QuantiteCour -= qte
                session.add(StockSortie(
                    IDTAnneeScolaire=id_annee, IDTArticle=stock.IDTArticle,
                    DateSort=maintenant.date(), QuantiteSort=qte, Prix_vente=prix,
                    HeureSortie=maintenant.time(), Login=login, ReferenceVente=reference,
                    PrixCatalogue=prix_catalogue,
                    RemiseMontant=(prix_catalogue - prix) * qte,
                    MotifRemise=motif_remise or None,
                    Statut="VALIDE",
                ))
            session.commit()
            return True, f"Vente de {len(lignes)} ligne(s) enregistree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement de la vente : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_journal_tickets(id_annee: Optional[int] = None) -> List[dict]:
        session = get_session()
        try:
            q = session.query(StockSortie).filter(StockSortie.ReferenceVente.isnot(None))
            if id_annee:
                q = q.filter(StockSortie.IDTAnneeScolaire == id_annee)
            rows = q.order_by(StockSortie.DateSort.desc(), StockSortie.HeureSortie.desc()).all()
            tickets = {}
            for row in rows:
                ticket = tickets.setdefault(row.ReferenceVente, {
                    "reference": row.ReferenceVente,
                    "date": row.DateSort,
                    "heure": row.HeureSortie,
                    "login": row.Login or "",
                    "statut": row.Statut or "VALIDE",
                    "lignes": 0,
                    "total": Decimal("0"),
                    "remise": Decimal("0"),
                })
                ticket["lignes"] += 1
                ticket["total"] += Decimal(row.Prix_vente or 0) * int(row.QuantiteSort or 0)
                ticket["remise"] += Decimal(row.RemiseMontant or 0)
            return list(tickets.values())
        finally:
            session.close()

    @staticmethod
    def get_ticket(reference: str) -> List[StockSortie]:
        session = get_session()
        try:
            return session.query(StockSortie).options(joinedload(StockSortie.article)).filter_by(
                ReferenceVente=reference
            ).order_by(StockSortie.IDStockSort.asc()).all()
        finally:
            session.close()

    @staticmethod
    def annuler_ticket(reference: str, motif: str) -> Tuple[bool, str]:
        allowed, msg = StockService._require_permission("KIOSQUE_REMBOURSEMENTS")
        if not allowed:
            return False, msg
        motif = (motif or "").strip()
        if not motif:
            return False, "Le motif d'annulation est obligatoire."
        session = get_session()
        try:
            lignes = session.query(StockSortie).filter_by(ReferenceVente=reference).order_by(
                StockSortie.IDTArticle
            ).with_for_update().all()
            if not lignes:
                return False, "Ticket introuvable."
            if any((ligne.Statut or "VALIDE") != "VALIDE" for ligne in lignes):
                return False, "Ce ticket est deja annule."
            ok, msg = StockService._validate_open_school_year(session, lignes[0].IDTAnneeScolaire)
            if not ok:
                return False, msg
            ids = sorted({ligne.IDTArticle for ligne in lignes})
            stocks = session.query(StockCour).filter(StockCour.IDTArticle.in_(ids)).order_by(
                StockCour.IDTArticle
            ).with_for_update().all()
            par_article = {stock.IDTArticle: stock for stock in stocks}
            for ligne in lignes:
                stock = par_article.get(ligne.IDTArticle)
                if not stock:
                    stock = StockCour(IDTArticle=ligne.IDTArticle, QuantiteCour=0)
                    session.add(stock)
                    par_article[ligne.IDTArticle] = stock
                stock.QuantiteCour += ligne.QuantiteSort
                ligne.Statut = "ANNULE"
                ligne.DateAnnulation = datetime.datetime.now()
                ligne.LoginAnnulation = StockService._current_login()
                ligne.MotifAnnulation = motif
            session.commit()
            return True, "Ticket annule et articles remis en stock."
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'annulation : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_alertes_stock() -> List[dict]:
        """Retourne la liste des articles dont le stock courant est inferieur ou egal au seuil d'alerte."""
        session = get_session()
        try:
            results = session.query(Article, StockCour).join(
                StockCour, Article.IDTArticle == StockCour.IDTArticle
            ).filter(StockCour.QuantiteCour <= Article.QTESeuil).all()

            alertes = []
            for art, sc in results:
                alertes.append({
                    "id_article": art.IDTArticle,
                    "libelle": art.Libelle,
                    "seuil": art.QTESeuil,
                    "stock": sc.QuantiteCour
                })
            return alertes
        except Exception as e:
            print(f"Erreur get_alertes_stock : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_stock_history_entrees(id_annee: Optional[int] = None, date_debut: Optional[datetime.date] = None, date_fin: Optional[datetime.date] = None) -> List[StockEntree]:
        """Historique des approvisionnements optionnellement filtres."""
        session = get_session()
        try:
            q = session.query(StockEntree).options(joinedload(StockEntree.article))
            if id_annee:
                q = q.filter_by(IDTAnneeScolaire=id_annee)
            if date_debut:
                q = q.filter(StockEntree.DateEnt >= date_debut)
            if date_fin:
                q = q.filter(StockEntree.DateEnt <= date_fin)
            return q.order_by(StockEntree.DateEnt.desc(), StockEntree.IDStockEnt.desc()).all()
        except Exception as e:
            print(f"Erreur get_stock_history_entrees : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_stock_history_sorties(id_annee: Optional[int] = None, date_debut: Optional[datetime.date] = None, date_fin: Optional[datetime.date] = None) -> List[StockSortie]:
        """Historique des ventes optionnellement filtres."""
        session = get_session()
        try:
            q = session.query(StockSortie).options(joinedload(StockSortie.article))
            if id_annee:
                q = q.filter_by(IDTAnneeScolaire=id_annee)
            if date_debut:
                q = q.filter(StockSortie.DateSort >= date_debut)
            if date_fin:
                q = q.filter(StockSortie.DateSort <= date_fin)
            return q.order_by(StockSortie.DateSort.desc(), StockSortie.HeureSortie.desc(), StockSortie.IDStockSort.desc()).all()
        except Exception as e:
            print(f"Erreur get_stock_history_sorties : {e}")
            return []
        finally:
            session.close()
