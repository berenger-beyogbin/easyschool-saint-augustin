from sqlalchemy import Column, Integer, String, Numeric, Boolean
from app.database import Base

class Article(Base):
    """
    Table representant les articles simples et les kits du Kiosque.
    Mappe de la table HFSQL 'TArticle'.

    Composition d'un KIT (D3) : table relationnelle KitArticle (voir
    models/kit_article.py), plus les anciennes colonnes texte ContenuKit/
    QteKit ("1;4;7" / "2;1;3").
    """
    __tablename__ = "TArticle"

    IDTArticle = Column(Integer, primary_key=True, autoincrement=True)
    Libelle = Column(String(100), nullable=False, unique=True)
    PU = Column(Numeric(12, 2), nullable=False, default=0.0)
    KIT = Column(Boolean, nullable=False, default=False)
    QTESeuil = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Article(ID={self.IDTArticle}, Libelle='{self.Libelle}', PU={self.PU}, KIT={self.KIT})>"
