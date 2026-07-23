from sqlalchemy import Column, Integer, String, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class KitAssemblage(Base):
    """Trace les articles consommés lors de la constitution d'un stock de kits."""
    __tablename__ = "KitAssemblage"
    __table_args__ = (
        CheckConstraint('"QuantiteKits" > 0', name="ck_assemblage_qte_kits_positive"),
        CheckConstraint('"QuantiteConsommee" > 0', name="ck_assemblage_qte_consommee_positive"),
    )

    IDKitAssemblage = Column(Integer, primary_key=True, autoincrement=True)
    IDStockEnt = Column(Integer, ForeignKey("StockEnt.IDStockEnt", ondelete="RESTRICT"), nullable=False)
    IDKit = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    IDArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    DateAssemblage = Column(Date, nullable=False)
    QuantiteKits = Column(Integer, nullable=False)
    QuantiteConsommee = Column(Integer, nullable=False)
    Login = Column(String(50), nullable=True)

    kit = relationship("Article", foreign_keys=[IDKit])
    article = relationship("Article", foreign_keys=[IDArticle])
