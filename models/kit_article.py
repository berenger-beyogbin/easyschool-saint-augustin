from sqlalchemy import Column, Integer, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class KitArticle(Base):
    """
    Ligne de composition d'un KIT (D3) : remplace les colonnes texte
    Article.ContenuKit/QteKit ("1;4;7" / "2;1;3") par une table relationnelle.

    IDKit -> ondelete CASCADE : la composition d'un KIT n'a aucun sens sans
    son KIT, elle disparait avec lui (contrairement aux tables historiques
    comme VenteLigne, ce n'est pas une piece financiere).
    IDArticleComposant -> ondelete RESTRICT : un article encore utilise dans
    la composition d'un KIT ne doit pas pouvoir etre supprime silencieusement.
    """
    __tablename__ = "KitArticle"

    __table_args__ = (
        CheckConstraint('"Quantite" > 0', name="ck_kit_article_quantite_positive"),
        UniqueConstraint("IDKit", "IDArticleComposant", name="uq_kit_article_kit_composant"),
    )

    IDKitArticle = Column(Integer, primary_key=True, autoincrement=True)
    IDKit = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="CASCADE"), nullable=False)
    IDArticleComposant = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    Quantite = Column(Integer, nullable=False)

    kit = relationship("Article", foreign_keys=[IDKit])
    composant = relationship("Article", foreign_keys=[IDArticleComposant])

    def __repr__(self):
        return f"<KitArticle(IDKit={self.IDKit}, IDArticleComposant={self.IDArticleComposant}, Quantite={self.Quantite})>"
