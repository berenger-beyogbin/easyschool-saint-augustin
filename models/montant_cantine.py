from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class MontantCantine(Base):
    """
    Frais de Cantine par niveau et annee scolaire.
    """
    __tablename__ = "MontantCant"

    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", "IDNiveau", name="uq_montant_cant_annee_niveau"),
    )

    IDMontantCant = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDNiveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="CASCADE"), nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False, default=0.0)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    niveau = relationship("TNiveau")

    def __repr__(self):
        return f"<MontantCantine(ID={self.IDMontantCant}, Niveau={self.IDNiveau}, Montant={self.Montant})>"
