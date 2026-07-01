from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TypeSortie(Base):
    """
    Table TypeSortie - types de sorties / types de mouvements comptables.
    """
    __tablename__ = "TypeSortie"

    IDTypeSortie = Column(Integer, primary_key=True, autoincrement=True)
    LibelleSortie = Column(String(100), nullable=False)
    IDCompte = Column(Integer, ForeignKey("Compte.IDCompte", ondelete="RESTRICT"), nullable=False)
    Sens = Column(String(10), nullable=False) # 'Debit' ou 'Credit'

    # Relation vers Compte
    compte = relationship("Compte")

    def __repr__(self):
        return f"<TypeSortie(ID={self.IDTypeSortie}, Libelle='{self.LibelleSortie}', CompteID={self.IDCompte}, Sens='{self.Sens}')>"
