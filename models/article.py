from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, CheckConstraint
from app.database import Base

class Article(Base):
    """
    Table representant les articles simples et les kits du Kiosque.
    Mappe de la table HFSQL 'TArticle'.
    """
    __tablename__ = "TArticle"
    __table_args__ = (
        CheckConstraint('"PU" >= 0', name="ck_article_pu_non_negatif"),
        CheckConstraint('"QTESeuil" >= 0', name="ck_article_seuil_non_negatif"),
    )

    IDTArticle = Column(Integer, primary_key=True, autoincrement=True)
    Libelle = Column(String(100), nullable=False, unique=True)
    PU = Column(Numeric(12, 2), nullable=False, default=0.0)
    KIT = Column(Boolean, nullable=False, default=False)
    QTESeuil = Column(Integer, nullable=False, default=0)
    ContenuKit = Column(Text, nullable=True) # Ex: "1;4;7"
    QteKit = Column(Text, nullable=True) # Ex: "2;1;3"

    def __repr__(self):
        return f"<Article(ID={self.IDTArticle}, Libelle='{self.Libelle}', PU={self.PU}, KIT={self.KIT})>"
