from typing import List, Tuple, Optional
from decimal import Decimal
from models.article import Article
from models.stock_entree import StockEntree
from models.stock_sortie import StockSortie
from services.article_service import ArticleService
from services.stock_service import StockService
from app.database import get_session

class KiosqueService:
    @staticmethod
    def vendre_article(id_art: int, qte: int, id_annee: int, prix_vente: float, login: str):
        return StockService.remove_stock(id_art, qte, id_annee, prix_vente, login)

    @staticmethod
    def vendre_style_article(id_art: int, qte: int, id_annee: int, prix_vente: float, login: str):
        return KiosqueService.vendre_article(id_art, qte, id_annee, prix_vente, login)

    @staticmethod
    def approvisionner_article(id_art: int, qte: int, id_annee: int, login: str) -> Tuple[bool, str]:
        """Proxy pour réapprovisionner un article."""
        return StockService.add_stock(id_art, qte, id_annee, login)

    @staticmethod
    def calcul_total_vente(id_art: int, quantite: int) -> float:
        """Calcule le montant total theoretique."""
        if quantite <= 0:
            return 0.0
        art = ArticleService.get_article_by_id(id_art)
        if art:
            return float(art.PU) * quantite
        return 0.0

    @staticmethod
    def get_articles_vendables() -> List[Article]:
        """Retourne tous les articles (simples et kits) disponibles."""
        return ArticleService.get_all_articles()

    @staticmethod
    def get_historique_ventes(id_annee: Optional[int] = None) -> List[StockSortie]:
        """proxy des ventes de l'année."""
        return StockService.get_stock_history_sorties(id_annee=id_annee)

    @staticmethod
    def get_historique_approvisionnements(id_annee: Optional[int] = None) -> List[StockEntree]:
        """proxy des approvisionnements de l'année."""
        return StockService.get_stock_history_entrees(id_annee=id_annee)
