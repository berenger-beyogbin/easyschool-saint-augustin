import threading

from app.database import get_session
from app.session import AppSession
from models.stock_cour import StockCour
from models.vente import Vente, VenteLigne
from services.vente_service import VenteService
from tests.factories import make_annee, make_article_avec_stock


def test_process_sale_success_debits_all_articles_atomically(db_session):
    annee = make_annee(db_session)
    art1, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    art2, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=5)

    cart = {
        art1.IDTArticle: {"nom": "Cahier", "qte": 3, "pu": 500},
        art2.IDTArticle: {"nom": "Stylo", "qte": 2, "pu": 200},
    }

    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is True
    sc1 = db_session.query(StockCour).filter_by(IDTArticle=art1.IDTArticle).first()
    sc2 = db_session.query(StockCour).filter_by(IDTArticle=art2.IDTArticle).first()
    assert sc1.QuantiteCour == 7
    assert sc2.QuantiteCour == 3
    assert db_session.query(Vente).count() == 1
    assert db_session.query(VenteLigne).count() == 2

    vente = db_session.query(Vente).first()
    assert vente.MontantTotal == 1900  # 3*500 + 2*200
    assert vente.ModePaiement == "Espèce"
    assert vente.Annule is False
    assert vente.NumeroRecu == f"V-{vente.IDVente:06d}"

    assert recu["numero_recu"] == vente.NumeroRecu
    assert recu["total"] == 1900
    assert len(recu["lignes"]) == 2


def test_process_sale_accepts_explicit_mode_paiement(db_session):
    annee = make_annee(db_session)
    art, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    cart = {art.IDTArticle: {"nom": "Cahier", "qte": 1, "pu": 500}}

    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier", mode_paiement="Mobile Money")

    assert ok is True
    assert recu["mode_paiement"] == "Mobile Money"


def test_process_sale_fails_atomically_when_one_article_insufficient(db_session):
    """Un panier de plusieurs articles echouant sur le dernier ne doit modifier
    AUCUN stock, pas meme ceux des articles qui avaient assez de stock, et ne
    doit creer ni Vente ni VenteLigne."""
    annee = make_annee(db_session)
    art1, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    art2, _ = make_article_avec_stock(db_session, libelle="Stylo", quantite=1)

    cart = {
        art1.IDTArticle: {"nom": "Cahier", "qte": 3, "pu": 500},
        art2.IDTArticle: {"nom": "Stylo", "qte": 5, "pu": 200},  # demande 5, dispo 1
    }

    ok, msg, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")

    assert ok is False
    assert recu is None
    assert "insuffisant" in msg.lower()

    sc1 = db_session.query(StockCour).filter_by(IDTArticle=art1.IDTArticle).first()
    sc2 = db_session.query(StockCour).filter_by(IDTArticle=art2.IDTArticle).first()
    assert sc1.QuantiteCour == 10  # inchange, malgre un stock suffisant pour cette ligne
    assert sc2.QuantiteCour == 1   # inchange
    assert db_session.query(Vente).count() == 0
    assert db_session.query(VenteLigne).count() == 0


def test_process_sale_rejects_empty_cart(db_session):
    annee = make_annee(db_session)
    ok, msg, recu = VenteService.process_sale({}, annee.IDTAnneeScolaire, "caissier")
    assert ok is False
    assert recu is None


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
        ok, msg, recu = VenteService.process_sale(cart, id_annee, "caissier")
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
        assert session.query(Vente).count() == 1
    finally:
        session.close()


def _make_vente(db_session, annee, montant=1000):
    art, _ = make_article_avec_stock(db_session, libelle="Cahier", quantite=10)
    cart = {art.IDTArticle: {"nom": "Cahier", "qte": 1, "pu": montant}}
    ok, _, recu = VenteService.process_sale(cart, annee.IDTAnneeScolaire, "caissier")
    assert ok is True
    return db_session.get(Vente, recu["id_vente"])


def test_annuler_vente_requires_motif(db_session):
    annee = make_annee(db_session)
    vente = _make_vente(db_session, annee)

    ok, msg = VenteService.annuler_vente(vente.IDVente, "", "admin")

    assert ok is False
    assert "motif" in msg.lower()


def test_annuler_vente_marks_record_and_is_idempotent_guarded(db_session):
    annee = make_annee(db_session)
    vente = _make_vente(db_session, annee)

    ok, msg = VenteService.annuler_vente(vente.IDVente, "Erreur de caisse", "admin")
    assert ok is True

    db_session.refresh(vente)
    assert vente.Annule is True
    assert vente.AnnulePar == "admin"
    assert vente.MotifAnnulation == "Erreur de caisse"
    assert vente.DateAnnulation is not None

    # Ne doit pas decrementer le stock une seconde fois (aucune restitution
    # automatique) ni pouvoir etre annulee deux fois.
    ok2, msg2 = VenteService.annuler_vente(vente.IDVente, "Nouvelle tentative", "admin")
    assert ok2 is False
    assert "deja annulee" in msg2.lower()


def test_annuler_vente_requires_permission(db_session):
    annee = make_annee(db_session)
    vente = _make_vente(db_session, annee)

    AppSession.set_current_user({"Login": "sans-droits", "Nom": "Sans Droits", "IsAdmin": False}, set())
    try:
        ok, msg = VenteService.annuler_vente(vente.IDVente, "Erreur", "sans-droits")
        assert ok is False
        assert "permission" in msg.lower()
    finally:
        AppSession.set_current_user(
            {"Login": "test-admin", "Nom": "Test", "IsAdmin": True}, set()
        )
