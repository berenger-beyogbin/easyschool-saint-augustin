import datetime
from typing import List, Tuple, Optional
from decimal import Decimal
from sqlalchemy.orm import joinedload
from models.article import Article
from models.stock_cour import StockCour
from models.stock_entree import StockEntree
from models.stock_sortie import StockSortie
from app.database import get_session

class StockService:
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
        """Augmente le stock courant d'un article et enregistre l'entree."""
        if qte <= 0:
            return False, "La quantite de reapprovisionnement doit etre strictement positive."
        if not id_annee:
            return False, "Aucune annee scolaire configuree active."

        session = get_session()
        try:
            sc = session.query(StockCour).filter_by(IDTArticle=id_art).first()
            if not sc:
                # Si jamais il n'existe pas, on le cree a la volee
                sc = StockCour(IDTArticle=id_art, QuantiteCour=0)
                session.add(sc)
            
            # Mise a jour
            sc.QuantiteCour += qte

            # Creation entree historic
            entree = StockEntree(
                IDTAnneeScolaire=id_annee,
                IDTArticle=id_art,
                DateEnt=date_ent or datetime.date.today(),
                QuantiteEnt=qte,
                Login=login
            )
            session.add(entree)
            session.commit()
            return True, f"Approvisionnement de {qte} unite(s) effectue avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de l'enregistrement de l'approvisionnement : {str(e)}"
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
        if prix_vente < 0:
            return False, "Le prix de vente ne doit pas etre negatif."
            
        session = get_session()
        try:
            sc = session.query(StockCour).filter_by(IDTArticle=id_art).first()
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
                Prix_vente=Decimal(str(prix_vente)),
                HeureSortie=now_time,
                Login=login
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
