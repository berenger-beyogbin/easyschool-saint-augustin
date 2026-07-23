from sqlalchemy import Column, Integer, String, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class StockEntree(Base):
    """
    Table representant l'historique d'approvisionnement des stocks du Kiosque.
    Mappe de la table HFSQL 'StockEnt'.
    """
    __tablename__ = "StockEnt"
    __table_args__ = (CheckConstraint('"QuantiteEnt" > 0', name="ck_stock_entree_positive"),)

    IDStockEnt = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDTArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    DateEnt = Column(Date, nullable=False)
    QuantiteEnt = Column(Integer, nullable=False)
    Login = Column(String(50), nullable=True)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    article = relationship("Article")

    def __repr__(self):
        return f"<StockEntree(ID={self.IDStockEnt}, IDTArticle={self.IDTArticle}, Date={self.DateEnt}, Quantite={self.QuantiteEnt})>"
