from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Time, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class StockSortie(Base):
    """
    Table representant les ventes et sorties d'articles du Kiosque.
    Mappe de la table HFSQL 'StockSortie'.
    """
    __tablename__ = "StockSortie"
    __table_args__ = (
        CheckConstraint('"QuantiteSort" > 0', name="ck_stock_sortie_positive"),
        CheckConstraint('"Prix_vente" >= 0', name="ck_stock_sortie_prix_non_negatif"),
    )

    IDStockSort = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDTArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    DateSort = Column(Date, nullable=False)
    QuantiteSort = Column(Integer, nullable=False)
    Prix_vente = Column(Numeric(12, 2), nullable=False)
    HeureSortie = Column(Time, nullable=False)
    Login = Column(String(50), nullable=True)
    ReferenceVente = Column(String(36), nullable=True)
    PrixCatalogue = Column(Numeric(12, 2), nullable=True)
    RemiseMontant = Column(Numeric(12, 2), nullable=False, default=0)
    MotifRemise = Column(String(255), nullable=True)
    Statut = Column(String(20), nullable=False, default="VALIDE")
    DateAnnulation = Column(DateTime, nullable=True)
    LoginAnnulation = Column(String(50), nullable=True)
    MotifAnnulation = Column(String(255), nullable=True)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    article = relationship("Article")

    def __repr__(self):
        return f"<StockSortie(ID={self.IDStockSort}, IDTArticle={self.IDTArticle}, Date={self.DateSort}, Qte={self.QuantiteSort}, Prix={self.Prix_vente})>"
