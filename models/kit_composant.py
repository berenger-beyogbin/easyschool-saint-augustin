from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class KitComposant(Base):
    __tablename__ = "KitComposant"
    __table_args__ = (
        UniqueConstraint("IDKit", "IDArticle", name="uq_kit_composant"),
        CheckConstraint('"Quantite" > 0', name="ck_kit_composant_positive"),
    )

    IDKitComposant = Column(Integer, primary_key=True, autoincrement=True)
    IDKit = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="CASCADE"), nullable=False)
    IDArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    Quantite = Column(Integer, nullable=False)

    kit = relationship("Article", foreign_keys=[IDKit])
    article = relationship("Article", foreign_keys=[IDArticle])
