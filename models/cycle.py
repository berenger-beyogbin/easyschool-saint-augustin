from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class TCycle(Base):
    """
    Table representative du cycle scolaire (Ex: Primaire, College, Lycee).
    Table temporaire proposee pour structurer proprement les niveaux.
    """
    __tablename__ = "TCycle"

    __table_args__ = (
        UniqueConstraint("Libelle", "IDAnneeScolaire", "IDEtablissement_Ecole", name="uq_cycle_lib_annee_etab"),
    )

    IDT_Cycle = Column(Integer, primary_key=True, autoincrement=True)
    Libelle = Column(String(50), nullable=False)
    
    # Cles etrangeres nullables (utilisees localement ou globalement par ecole/annee)
    IDEtablissement_Ecole = Column(Integer, ForeignKey("Etablissement_Ecole.IDEtablissement_Ecole", ondelete="SET NULL"), nullable=True)
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="SET NULL"), nullable=True)

    # Relations
    niveaux = relationship("TNiveau", back_populates="cycle")
    classes = relationship("TClasse", back_populates="cycle")

    def __repr__(self):
        return f"<TCycle(ID={self.IDT_Cycle}, Libelle='{self.Libelle}')>"
