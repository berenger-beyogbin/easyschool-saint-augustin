from decimal import Decimal

from app.session import AppSession
from models.article import Article
from models.stock_cour import StockCour
from models.stock_sortie import StockSortie
from models.kit_composant import KitComposant
from models.kit_assemblage import KitAssemblage
from services.article_service import ArticleService
from services.stock_service import StockService
from tests.factories import make_annee


def _set_kiosque_user():
    AppSession.set_current_user(
        {
            "IDUtilisateur": 3001,
            "Login": "kiosque_test",
            "Nom": "Kiosque",
            "ProfilCode": "KIOSQUE",
            "ProfilLibelle": "Kiosque",
            "IsAdmin": False,
        },
        permissions={
            "KIOSQUE_STOCKS", "KIOSQUE_VENTES", "KIOSQUE_ARTICLES",
            "KIOSQUE_REMISES", "KIOSQUE_REMBOURSEMENTS",
        },
    )


def _make_article_with_stock(db_session, qte=0, libelle="Cahier test", pu=500):
    _set_kiosque_user()
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


def test_sale_cart_is_atomic_when_one_line_has_insufficient_stock(db_session):
    annee = make_annee(db_session)
    article_ok, stock_ok = _make_article_with_stock(db_session, qte=5, libelle="Cahier panier")
    article_ko, stock_ko = _make_article_with_stock(db_session, qte=1, libelle="Stylo panier")

    ok, msg = StockService.enregistrer_panier({
        article_ok.IDTArticle: {"qte": 2, "pu": 500},
        article_ko.IDTArticle: {"qte": 2, "pu": 500},
    }, annee.IDTAnneeScolaire)

    db_session.expire_all()
    assert ok is False
    assert "disponible" in msg
    assert db_session.get(StockCour, stock_ok.IDStockCour).QuantiteCour == 5
    assert db_session.get(StockCour, stock_ko.IDStockCour).QuantiteCour == 1
    assert db_session.query(StockSortie).count() == 0


def test_sale_cart_groups_lines_under_one_reference(db_session):
    annee = make_annee(db_session)
    article_a, _ = _make_article_with_stock(db_session, qte=3, libelle="Article A")
    article_b, _ = _make_article_with_stock(db_session, qte=3, libelle="Article B")

    ok, msg = StockService.enregistrer_panier({
        article_a.IDTArticle: {"qte": 1, "pu": 500},
        article_b.IDTArticle: {"qte": 2, "pu": 500},
    }, annee.IDTAnneeScolaire)

    assert ok is True, msg
    sorties = db_session.query(StockSortie).all()
    assert len(sorties) == 2
    assert sorties[0].ReferenceVente
    assert sorties[0].ReferenceVente == sorties[1].ReferenceVente


def test_discount_is_audited_and_ticket_can_be_cancelled(db_session):
    annee = make_annee(db_session)
    article, stock = _make_article_with_stock(db_session, qte=4, libelle="Article remise", pu=1000)
    ok, msg = StockService.enregistrer_panier({
        article.IDTArticle: {"qte": 2, "pu": 900, "motif_remise": "Geste commercial"},
    }, annee.IDTAnneeScolaire)
    assert ok is True, msg
    sortie = db_session.query(StockSortie).one()
    assert sortie.PrixCatalogue == Decimal("1000")
    assert sortie.RemiseMontant == Decimal("200")
    assert sortie.MotifRemise == "Geste commercial"

    ok, msg = StockService.annuler_ticket(sortie.ReferenceVente, "Erreur de saisie")
    assert ok is True, msg
    db_session.expire_all()
    assert db_session.get(StockCour, stock.IDStockCour).QuantiteCour == 4
    assert db_session.query(StockSortie).one().Statut == "ANNULE"


def test_kit_composition_is_persisted_in_relational_table(db_session):
    article_a, _ = _make_article_with_stock(db_session, libelle="Composant A")
    article_b, _ = _make_article_with_stock(db_session, libelle="Composant B")
    ok, msg = ArticleService.create_kit(
        "Kit relationnel", 2500, 1,
        f"{article_a.IDTArticle};{article_b.IDTArticle}", "2;1",
    )
    assert ok is True, msg
    composants = db_session.query(KitComposant).order_by(KitComposant.IDArticle).all()
    assert [(c.IDArticle, c.Quantite) for c in composants] == [
        (article_a.IDTArticle, 2), (article_b.IDTArticle, 1)
    ]


def test_kit_restock_consumes_components_atomically(db_session):
    annee = make_annee(db_session)
    article_a, stock_a = _make_article_with_stock(db_session, qte=10, libelle="Composant stock A")
    article_b, stock_b = _make_article_with_stock(db_session, qte=8, libelle="Composant stock B")
    ok, msg = ArticleService.create_kit(
        "Kit à assembler", 3000, 1,
        f"{article_a.IDTArticle};{article_b.IDTArticle}", "2;1",
    )
    assert ok is True, msg
    kit = db_session.query(Article).filter_by(Libelle="Kit à assembler").one()

    ok, msg = StockService.add_stock(kit.IDTArticle, 4, annee.IDTAnneeScolaire, "IGNORED")
    assert ok is True, msg
    db_session.expire_all()
    assert db_session.get(StockCour, stock_a.IDStockCour).QuantiteCour == 2
    assert db_session.get(StockCour, stock_b.IDStockCour).QuantiteCour == 4
    assert db_session.query(StockCour).filter_by(IDTArticle=kit.IDTArticle).one().QuantiteCour == 4
    assert sorted(a.QuantiteConsommee for a in db_session.query(KitAssemblage).all()) == [4, 8]


def test_kit_restock_refuses_all_changes_if_one_component_is_insufficient(db_session):
    annee = make_annee(db_session)
    article_a, stock_a = _make_article_with_stock(db_session, qte=10, libelle="Composant suffisant")
    article_b, stock_b = _make_article_with_stock(db_session, qte=1, libelle="Composant insuffisant")
    ok, msg = ArticleService.create_kit(
        "Kit bloqué", 3000, 1,
        f"{article_a.IDTArticle};{article_b.IDTArticle}", "2;1",
    )
    assert ok is True, msg
    kit = db_session.query(Article).filter_by(Libelle="Kit bloqué").one()

    ok, msg = StockService.add_stock(kit.IDTArticle, 2, annee.IDTAnneeScolaire, "IGNORED")
    assert ok is False
    assert "insuffisant" in msg.lower()
    db_session.expire_all()
    assert db_session.get(StockCour, stock_a.IDStockCour).QuantiteCour == 10
    assert db_session.get(StockCour, stock_b.IDStockCour).QuantiteCour == 1
    assert db_session.query(StockCour).filter_by(IDTArticle=kit.IDTArticle).one().QuantiteCour == 0
    assert db_session.query(KitAssemblage).count() == 0
