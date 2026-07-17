import threading

from app.database import get_session
from models.stock_cour import StockCour
from models.stock_sortie import StockSortie
from services.stock_service import StockService
from tests.factories import make_annee, make_article_avec_stock


def test_process_sale_success_debits_all_articles_atomically(db_session):
    annee = make_annee(db_session)
    art1, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    art2, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=5)

    cart = {
        art1.IDTArticle: {"nom": "Cahier", "qte": 3, "pu": 500},
        art2.IDTArticle: {"nom": "Stylo", "qte": 2, "pu": 200},
    }

    ok, msg = StockService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is True
    sc1 = db_session.query(StockCour).filter_by(IDTArticle=art1.IDTArticle).first()
    sc2 = db_session.query(StockCour).filter_by(IDTArticle=art2.IDTArticle).first()
    assert sc1.QuantiteCour == 7
    assert sc2.QuantiteCour == 3
    assert db_session.query(StockSortie).count() == 2


def test_process_sale_fails_atomically_when_one_article_insufficient(db_session):
    """Un panier de plusieurs articles echouant sur le dernier ne doit modifier
    AUCUN stock, pas meme ceux des articles qui avaient assez de stock."""
    annee = make_annee(db_session)
    art1, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    art2, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=1)

    cart = {
        art1.IDTArticle: {"nom": "Cahier", "qte": 3, "pu": 500},
        art2.IDTArticle: {"nom": "Stylo", "qte": 5, "pu": 200},  # demande 5, dispo 1
    }

    ok, msg = StockService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is False
    assert "insuffisant" in msg.lower()

    sc1 = db_session.query(StockCour).filter_by(IDTArticle=art1.IDTArticle).first()
    sc2 = db_session.query(StockCour).filter_by(IDTArticle=art2.IDTArticle).first()
    assert sc1.QuantiteCour == 10  # inchange, malgre un stock suffisant pour cette ligne
    assert sc2.QuantiteCour == 1   # inchange
    assert db_session.query(StockSortie).count() == 0


def test_process_sale_rejects_empty_cart(db_session):
    annee = make_annee(db_session)
    ok, msg = StockService.process_sale({}, annee.IDTAnneeScolaire, "caissier")
    assert ok is False


def test_process_sale_concurrent_never_oversells(db_session):
    """Deux ventes concurrentes de 4 unites chacune sur un stock de 5 ne
    doivent jamais toutes les deux reussir (recette #4)."""
    annee = make_annee(db_session)
    art, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=5)
    db_session.commit()

    id_annee = annee.IDTAnneeScolaire
    id_art = art.IDTArticle
    results = []
    lock = threading.Lock()

    def vendre():
        cart = {id_art: {"nom": "Cahier", "qte": 4, "pu": 500}}
        ok, msg = StockService.process_sale(cart, id_annee, "caissier")
        with lock:
            results.append(ok)

    t1 = threading.Thread(target=vendre)
    t2 = threading.Thread(target=vendre)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results.count(True) == 1
    assert results.count(False) == 1

    session = get_session()
    try:
        sc = session.query(StockCour).filter_by(IDTArticle=id_art).first()
        assert sc.QuantiteCour == 1  # 5 - 4, jamais negatif, une seule vente passee
    finally:
        session.close()
