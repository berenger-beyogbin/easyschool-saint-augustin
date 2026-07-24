from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class StockEntree(Base):
    """
    Table representant l'historique d'approvisionnement des stocks du Kiosque.
    Mappe de la table HFSQL 'StockEnt'.
    """
    __tablename__ = "StockEnt"

    IDStockEnt = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : un mouvement de stock est un historique
    # d'approvisionnement, il ne doit pas disparaitre avec l'annee ou l'article.
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
