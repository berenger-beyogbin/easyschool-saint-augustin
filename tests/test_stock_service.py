from decimal import Decimal

from models.article import Article
from models.stock_cour import StockCour
from services.stock_service import StockService
from tests.factories import make_annee


def _make_article_with_stock(db_session, qte=0, libelle="Cahier test", pu=500):
    article = Article(
        Libelle=libelle,
        PU=Decimal(str(pu)),
        KIT=False,
        QTESeuil=1,
    )
    db_session.add(article)
    db_session.commit()

    stock = StockCour(IDTArticle=article.IDTArticle, QuantiteCour=qte)
    db_session.add(stock)
    db_session.commit()
    return article, stock


def test_remove_stock_refuses_insufficient_quantity_and_preserves_current_stock(db_session):
    annee = make_annee(db_session)
    article, stock = _make_article_with_stock(db_session, qte=2)

    ok, msg = StockService.remove_stock(
        article.IDTArticle,
        qte=3,
        id_annee=annee.IDTAnneeScolaire,
        prix_vente=500,
        login="TEST",
    )

    db_session.expire_all()
    assert ok is False
    assert "stock insuffisant" in msg.lower()
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 2


def test_add_stock_refuses_closed_school_year(db_session):
    annee = make_annee(db_session, cloturer=True)
    article, stock = _make_article_with_stock(db_session, qte=0, libelle="Stylo test")

    ok, msg = StockService.add_stock(
        article.IDTArticle,
        qte=5,
        id_annee=annee.IDTAnneeScolaire,
        login="TEST",
    )

    db_session.expire_all()
    assert ok is False
    assert "clotur" in msg.lower() or "clôtur" in msg.lower()
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 0


def test_remove_stock_refuses_closed_school_year_and_preserves_current_stock(db_session):
    annee = make_annee(db_session, cloturer=True)
    article, stock = _make_article_with_stock(db_session, qte=4, libelle="Livre test")

    ok, msg = StockService.remove_stock(
        article.IDTArticle,
        qte=1,
        id_annee=annee.IDTAnneeScolaire,
        prix_vente=1000,
        login="TEST",
    )

    db_session.expire_all()
    assert ok is False
    assert "clotur" in msg.lower() or "clôtur" in msg.lower()
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 4
