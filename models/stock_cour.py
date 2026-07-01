from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class StockCour(Base):
    """
    Table representant le stock courant de chaque article du Kiosque.
    Mappe de la table HFSQL 'StockCour'.
    """
    __tablename__ = "StockCour"

    IDStockCour = Column(Integer, primary_key=True, autoincrement=True)
    IDTArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="CASCADE"), nullable=False, unique=True)
    QuantiteCour = Column(Integer, nullable=False, default=0)

    # Relation
    article = relationship("Article")

    def __repr__(self):
        return f"<StockCour(ID={self.IDStockCour}, IDTArticle={self.IDTArticle}, QuantiteCour={self.QuantiteCour})>"
