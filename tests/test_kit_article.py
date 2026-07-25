from models.article import Article
from models.kit_article import KitArticle
from models.stock_cour import StockCour
from services.article_service import ArticleService
from services.stock_service import StockService
from services.vente_service import VenteService
from tests.factories import make_annee, make_article_avec_stock, make_kit


# ===========================================================================
# ArticleService.create_kit / update_article / delete_article
# ===========================================================================

def test_create_kit_builds_kit_article_rows_and_no_stock_cour(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    stylo, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=10)

    ok, msg = ArticleService.create_kit(
        "Trousseau", 2000, 0, {cahier.IDTArticle: 3, stylo.IDTArticle: 2}
    )

    assert ok is True
    kit = db_session.query(Article).filter_by(Libelle="Trousseau").first()
    assert kit is not None
    assert kit.KIT is True

    lignes = db_session.query(KitArticle).filter_by(IDKit=kit.IDTArticle).all()
    assert {(ligne.IDArticleComposant, ligne.Quantite) for ligne in lignes} == {
        (cahier.IDTArticle, 3), (stylo.IDTArticle, 2)
    }

    # Un KIT n'a plus sa propre ligne de stock (D3).
    assert db_session.query(StockCour).filter_by(IDTArticle=kit.IDTArticle).first() is None


def test_create_kit_rejects_empty_composition(db_session):
    ok, msg = ArticleService.create_kit("Trousseau", 2000, 0, {})
    assert ok is False
    assert "au moins un article" in msg.lower()


def test_create_kit_rejects_nonexistent_component(db_session):
    ok, msg = ArticleService.create_kit("Trousseau", 2000, 0, {999999: 1})
    assert ok is False
    assert "introuvable" in msg.lower()


def test_create_kit_rejects_kit_as_component(db_session):
    interieur = make_kit(db_session, libelle="Kit Interieur")
    ok, msg = ArticleService.create_kit("Kit Exterieur", 2000, 0, {interieur.IDTArticle: 1})
    assert ok is False
    assert "kit" in msg.lower()


def test_create_kit_rejects_non_positive_quantity(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    ok, msg = ArticleService.create_kit("Trousseau", 2000, 0, {cahier.IDTArticle: 0})
    assert ok is False


def test_update_article_replaces_kit_composition(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    stylo, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=10)
    regle, _ = make_article_avec_stock(db_session, libelle="Regle", quantite=10)
    kit = make_kit(db_session, libelle="Trousseau", composition={cahier.IDTArticle: 3})

    ok, msg = ArticleService.update_article(
        kit.IDTArticle, "Trousseau", 2500, 0,
        composition={stylo.IDTArticle: 1, regle.IDTArticle: 2}, is_kit=True,
    )

    assert ok is True
    lignes = db_session.query(KitArticle).filter_by(IDKit=kit.IDTArticle).all()
    assert {(ligne.IDArticleComposant, ligne.Quantite) for ligne in lignes} == {
        (stylo.IDTArticle, 1), (regle.IDTArticle, 2)
    }


def test_delete_article_blocked_when_referenced_by_kit_composition(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    make_kit(db_session, libelle="Trousseau", composition={cahier.IDTArticle: 3})

    ok, msg = ArticleService.delete_article(cahier.IDTArticle)

    assert ok is False
    assert "kit" in msg.lower()


def test_delete_kit_cascades_its_composition_rows(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    kit = make_kit(db_session, libelle="Trousseau", composition={cahier.IDTArticle: 3})

    ok, msg = ArticleService.delete_article(kit.IDTArticle)

    assert ok is True
    assert db_session.query(KitArticle).filter_by(IDKit=kit.IDTArticle).count() == 0
    # Le composant lui-meme n'est pas touche.
    assert db_session.get(Article, cahier.IDTArticle) is not None


# ===========================================================================
# StockService.get_stock_disponible
# ===========================================================================

def test_get_stock_disponible_simple_article_reads_stock_cour(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=7)
    assert StockService.get_stock_disponible(cahier.IDTArticle) == 7


def test_get_stock_disponible_kit_is_minimum_across_components(db_session):
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)  # 10 // 3 = 3
    stylo, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=5)     # 5 // 2 = 2
    kit = make_kit(db_session, composition={cahier.IDTArticle: 3, stylo.IDTArticle: 2})

    assert StockService.get_stock_disponible(kit.IDTArticle) == 2


def test_get_stock_disponible_kit_without_composition_is_zero(db_session):
    kit = make_kit(db_session, composition=None)
    assert StockService.get_stock_disponible(kit.IDTArticle) == 0


# ===========================================================================
# VenteService.process_sale avec KITs
# ===========================================================================

def test_process_sale_kit_decrements_components_not_a_kit_stock(db_session):
    annee = make_annee(db_session)
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    stylo, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=10)
    kit = make_kit(db_session, libelle="Trousseau", pu=2000,
                    composition={cahier.IDTArticle: 3, stylo.IDTArticle: 2})

    cart = {kit.IDTArticle: {"nom": "Trousseau", "qte": 2, "pu": 2000}}
    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is True
    cahier_stock = db_session.query(StockCour).filter_by(IDTArticle=cahier.IDTArticle).first()
    stylo_stock = db_session.query(StockCour).filter_by(IDTArticle=stylo.IDTArticle).first()
    assert cahier_stock.QuantiteCour == 10 - 3 * 2  # 4
    assert stylo_stock.QuantiteCour == 10 - 2 * 2   # 6

    # Une seule VenteLigne pour le KIT (pas une par composant), et son propre
    # StockCour (inexistant) n'est evidemment pas cree/touche.
    assert len(recu["lignes"]) == 1
    assert recu["lignes"][0]["nom"] == "Trousseau"
    assert recu["total"] == 4000


def test_process_sale_kit_insufficient_component_rolls_back_atomically(db_session):
    annee = make_annee(db_session)
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=5)  # insuffisant pour 2 KITs de 3
    stylo, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=10)
    kit = make_kit(db_session, libelle="Trousseau", pu=2000,
                    composition={cahier.IDTArticle: 3, stylo.IDTArticle: 2})

    cart = {kit.IDTArticle: {"nom": "Trousseau", "qte": 2, "pu": 2000}}
    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is False
    assert recu is None
    assert "insuffisant" in msg.lower()
    assert "Cahier" in msg

    cahier_stock = db_session.query(StockCour).filter_by(IDTArticle=cahier.IDTArticle).first()
    stylo_stock = db_session.query(StockCour).filter_by(IDTArticle=stylo.IDTArticle).first()
    assert cahier_stock.QuantiteCour == 5    # inchange
    assert stylo_stock.QuantiteCour == 10    # inchange (aucune ecriture partielle)
    assert db_session.query(KitArticle).count() == 2  # composition intacte
    from models.vente import Vente
    assert db_session.query(Vente).count() == 0


def test_process_sale_mixed_cart_sums_shared_component_once(db_session):
    """Le meme article vendu a la fois seul et via un KIT ne doit etre
    decompte qu'une seule fois, pour le total combine des deux besoins."""
    annee = make_annee(db_session)
    cahier, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    kit = make_kit(db_session, libelle="Trousseau", pu=2000, composition={cahier.IDTArticle: 3})

    cart = {
        kit.IDTArticle: {"nom": "Trousseau", "qte": 1, "pu": 2000},
        cahier.IDTArticle: {"nom": "Cahier", "qte": 2, "pu": 500},
    }
    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is True
    cahier_stock = db_session.query(StockCour).filter_by(IDTArticle=cahier.IDTArticle).first()
    # 3 (via le KIT) + 2 (vendu seul) = 5 debites d'un coup.
    assert cahier_stock.QuantiteCour == 5
    assert len(recu["lignes"]) == 2
