from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class TNiveau(Base):
    """
    Table representant les niveaux scolaires (Ex: CP1, CE1, CM2).
    Mappe de la table HFSQL 'TNiveau'.
    """
    __tablename__ = "TNiveau"

    __table_args__ = (
        UniqueConstraint("Libelle", "IDT_Cycle", "IDAnneeScolaire", "IDEtablissement_Ecole", name="uq_niveau_lib_cycle_annee_etab"),
    )

    IDT_Niveau = Column(Integer, primary_key=True, autoincrement=True)
    IDT_Cycle = Column(Integer, ForeignKey("TCycle.IDT_Cycle", ondelete="CASCADE"), nullable=False)
    Libelle = Column(String(50), nullable=False)
    IDEtablissement_Ecole = Column(Integer, ForeignKey("Etablissement_Ecole.IDEtablissement_Ecole", ondelete="CASCADE"), nullable=True)
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=True)

    # Relations SQLAlchemy
    cycle = relationship("TCycle", back_populates="niveaux")
    annee_scolaire = relationship("TAnneeScolaire", back_populates="niveaux")
    classes = relationship("TClasse", back_populates="niveau")

    def __repr__(self):
        return f"<TNiveau(ID={self.IDT_Niveau}, Libelle='{self.Libelle}')>"
