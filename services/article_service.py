from typing import List, Tuple, Optional
from decimal import Decimal
from models.article import Article
from models.stock_cour import StockCour
from models.stock_entree import StockEntree
from models.stock_sortie import StockSortie
from app.database import get_session

class ArticleService:
    @staticmethod
    def get_all_articles() -> List[Article]:
        """Recupere tous les articles (simples et kits) tries par Libelle."""
        session = get_session()
        try:
            return session.query(Article).order_by(Article.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur get_all_articles : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_articles_simples() -> List[Article]:
        """Recupere uniquement les articles simples (KIT = False)."""
        session = get_session()
        try:
            return session.query(Article).filter(Article.KIT == False).order_by(Article.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur get_articles_simples : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_kits() -> List[Article]:
        """Recupere uniquement les kits (KIT = True)."""
        session = get_session()
        try:
            return session.query(Article).filter(Article.KIT == True).order_by(Article.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur get_kits : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def get_article_by_id(id_art: int) -> Optional[Article]:
        """Recupere un article par son ID."""
        session = get_session()
        try:
            return session.query(Article).get(id_art)
        except Exception as e:
            print(f"Erreur get_article_by_id : {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def search_articles(query: str) -> List[Article]:
        """Recherche des articles par libelle."""
        if not query:
            return ArticleService.get_all_articles()
        session = get_session()
        try:
            return session.query(Article).filter(
                Article.Libelle.ilike(f"%{query}%")
            ).order_by(Article.Libelle.asc()).all()
        except Exception as e:
            print(f"Erreur search_articles : {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def create_article(libelle: str, pu: float, seuil: int) -> Tuple[bool, str]:
        """Cree un nouvel article simple et initialise son stock a 0."""
        if not libelle or not libelle.strip():
            return False, "Le libelle de l'article est obligatoire."
        if pu < 0:
            return False, "Le prix unitaire ne peut pas etre negatif."
        if seuil < 0:
            return False, "Le seuil d'alerte de stock ne peut pas etre negatif."

        lib_clean = libelle.strip()
        session = get_session()
        try:
            # Verification unicite du libelle
            exist = session.query(Article).filter(Article.Libelle.ilike(lib_clean)).first()
            if exist:
                return False, f"Un article ou un kit intitule '{lib_clean}' existe deja."

            nouveau = Article(
                Libelle=lib_clean,
                PU=Decimal(str(pu)),
                KIT=False,
                QTESeuil=seuil
            )
            session.add(nouveau)
            session.flush() # Recupere l'ID genere

            # Initialisation automatique du stock courant a 0
            stock = StockCour(IDTArticle=nouveau.IDTArticle, QuantiteCour=0)
            session.add(stock)

            session.commit()
            return True, "Article simple cree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la creation de l'article : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def create_kit(libelle: str, pu: float, seuil: int, contenu_kit: str, qte_kit: str) -> Tuple[bool, str]:
        """Cree un nouveau kit d'articles et initialise son stock a 0."""
        if not libelle or not libelle.strip():
            return False, "Le libelle du kit est obligatoire."
        if pu < 0:
            return False, "Le prix unitaire du kit ne peut pas etre negatif."
        if seuil < 0:
            return False, "Le seuil d'alerte de stock ne peut pas etre negatif."

        lib_clean = libelle.strip()
        session = get_session()
        try:
            # Verification unicite du libelle
            exist = session.query(Article).filter(Article.Libelle.ilike(lib_clean)).first()
            if exist:
                return False, f"Un article ou un kit intitule '{lib_clean}' existe deja."

            nouveau = Article(
                Libelle=lib_clean,
                PU=Decimal(str(pu)),
                KIT=True,
                QTESeuil=seuil,
                ContenuKit=contenu_kit,
                QteKit=qte_kit
            )
            session.add(nouveau)
            session.flush()

            # Initialisation automatique du stock courant a 0
            stock = StockCour(IDTArticle=nouveau.IDTArticle, QuantiteCour=0)
            session.add(stock)

            session.commit()
            return True, "Kit cree avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la creation du kit : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_article(id_art: int, libelle: str, pu: float, seuil: int, contenu_kit: Optional[str] = None, qte_kit: Optional[str] = None, is_kit: bool = False) -> Tuple[bool, str]:
        """Met a jour un article existant."""
        if not libelle or not libelle.strip():
            return False, "Le libelle est obligatoire."
        if pu < 0:
            return False, "Le prix unitaire ne peut pas etre negatif."
        if seuil < 0:
            return False, "Le seuil de stock ne peut pas etre negatif."

        lib_clean = libelle.strip()
        session = get_session()
        try:
            art = session.query(Article).get(id_art)
            if not art:
                return False, "Article inexistant."

            # Verification unicite libelle hors lui-meme
            exist = session.query(Article).filter(
                (Article.Libelle.ilike(lib_clean)) & (Article.IDTArticle != id_art)
            ).first()
            if exist:
                return False, f"Un autre article porte deja le libelle '{lib_clean}'."

            art.Libelle = lib_clean
            art.PU = Decimal(str(pu))
            art.QTESeuil = seuil
            art.KIT = is_kit
            
            if is_kit:
                art.ContenuKit = contenu_kit
                art.QteKit = qte_kit
            else:
                art.ContenuKit = None
                art.QteKit = None

            session.commit()
            return True, "Article/Kit mis a jour avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la mise a jour de l'article : {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_article(id_art: int) -> Tuple[bool, str]:
        """Supprime un article s'il n'a pas de mouvements ni de stock courant positif."""
        session = get_session()
        try:
            art = session.query(Article).get(id_art)
            if not art:
                return False, "Article inexistant."

            # 1. Verifier si l'article est utilise dans un Kit
            kits = session.query(Article).filter(Article.KIT == True).all()
            for kit in kits:
                if kit.ContenuKit:
                    ids = [x.strip() for x in kit.ContenuKit.split(";") if x.strip()]
                    if str(id_art) in ids:
                        return False, "Impossible de supprimer cet article car il est utilisé dans la composition d’un kit."

            # 2. Verifier si le stock courant est > 0
            sc = session.query(StockCour).filter_by(IDTArticle=id_art).first()
            if sc and sc.QuantiteCour > 0:
                return False, f"Impossible de supprimer l'article car son stock courant est de {sc.QuantiteCour} unite(s)."

            # 2. Verifier si l'article est associe a des entrees de stock
            entrees = session.query(StockEntree).filter_by(IDTArticle=id_art).count()
            if entrees > 0:
                return False, "Impossible de supprimer cet article car il contient des historiques d'approvisionnement (StockEnt)."

            # 3. Verifier si l'article est associe a des sorties (ventes) de stock
            sorties = session.query(StockSortie).filter_by(IDTArticle=id_art).count()
            if sorties > 0:
                return False, "Impossible de supprimer cet article car il contient des historiques de vente (StockSortie)."

            # Tout est propre, on supprime le stock_cour lie puis l'article
            if sc:
                session.delete(sc)
            session.delete(art)
            session.commit()
            return True, "Article/Kit supprime avec succes !"
        except Exception as e:
            session.rollback()
            return False, f"Erreur lors de la suppression de l'article : {str(e)}"
        finally:
            session.close()
