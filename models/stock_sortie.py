from sqlalchemy import Column, Integer, String, Date, Numeric, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class StockSortie(Base):
    """
    Table representant les ventes et sorties d'articles du Kiosque.
    Mappe de la table HFSQL 'StockSortie'.
    """
    __tablename__ = "StockSortie"

    IDStockSort = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : une vente/sortie de stock est une piece financiere
    # et un historique, elle ne doit pas disparaitre avec l'annee ou l'article.
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDTArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    DateSort = Column(Date, nullable=False)
    QuantiteSort = Column(Integer, nullable=False)
    Prix_vente = Column(Numeric(12, 2), nullable=False)
    HeureSortie = Column(Time, nullable=False)
    Login = Column(String(50), nullable=True)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    article = relationship("Article")

    def __repr__(self):
        return f"<StockSortie(ID={self.IDStockSort}, IDTArticle={self.IDTArticle}, Date={self.DateSort}, Qte={self.QuantiteSort}, Prix={self.Prix_vente})>"
