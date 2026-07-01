from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class MontantScol(Base):
    """
    Parametrage des montants de scolarite par niveau et annee scolaire.
    """
    __tablename__ = "MontantScol"

    __table_args__ = (
        UniqueConstraint("IDTAnneeScolaire", "IDNiveau", name="uq_montant_scol_annee_niveau"),
    )

    IDMontantScol = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDNiveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="CASCADE"), nullable=False)
    Montant = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantEnsPri = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantEnsSecondaire = Column(Numeric(12, 2), nullable=False, default=0.0)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    niveau = relationship("TNiveau")

    def __repr__(self):
        return f"<MontantScol(ID={self.IDMontantScol}, Niveau={self.IDNiveau}, Montant={self.Montant})>"
