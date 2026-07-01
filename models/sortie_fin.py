from sqlalchemy import Column, Integer, String, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class SortieFin(Base):
    """
    Table SortieFin - Mouvements financiers de la comptabilite (Debit / Credit).
    """
    __tablename__ = "SortieFin"

    IDSortieFin = Column(Integer, primary_key=True, autoincrement=True)
    Benef = Column(String(100), nullable=False)
    Detail = Column(Text, nullable=True)
    Montant = Column(Numeric(12, 2), nullable=False)
    NumBenef = Column(String(30), nullable=True)
    DateSortie = Column(Date, nullable=False)
    Login = Column(String(50), nullable=True)
    CodeSortie = Column(String(50), nullable=True)
    IDAnSco = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    DebitCredit = Column(String(10), nullable=False) # 'Debit' ou 'Credit'
    IDCompte = Column(Integer, ForeignKey("Compte.IDCompte", ondelete="RESTRICT"), nullable=False)

    # Relations
    compte = relationship("Compte")
    annee_scolaire = relationship("TAnneeScolaire")

    def __repr__(self):
        return f"<SortieFin(ID={self.IDSortieFin}, Code='{self.CodeSortie}', Benef='{self.Benef}', Montant={self.Montant}, Sens='{self.DebitCredit}')>"
