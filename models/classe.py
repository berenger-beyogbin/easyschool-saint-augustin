from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class TClasse(Base):
    """
    Table representative de la classe d'eleves (Ex: CP1 A, CM2 B).
    Mappe de la table HFSQL 'TClasse'.
    """
    __tablename__ = "TClasse"

    __table_args__ = (
        UniqueConstraint("LibClasse", "IDT_Niveau", "IDAnneeScolaire", "IDEtablissement_Ecole", name="uq_classe_lib_niveau_annee_etab"),
    )

    IDTClasse = Column(Integer, primary_key=True, autoincrement=True)
    Sigle = Column(String(10)) # Sigle court (Ex: CP1A)
    LibClasse = Column(String(50), nullable=False) # Libelle complet (Ex: CP1 Or)
    
    IDOrdreEnseignement = Column(Integer, nullable=True) # Pour classer les ordres d'ecole
    IDT_Cycle = Column(Integer, ForeignKey("TCycle.IDT_Cycle", ondelete="RESTRICT"), nullable=True)
    IDT_Niveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="RESTRICT"), nullable=False)
    Capacite = Column(Integer, default=40)
    
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=True)
    IDEtablissement_Ecole = Column(Integer, ForeignKey("Etablissement_Ecole.IDEtablissement_Ecole", ondelete="CASCADE"), nullable=True)

    # Relations SQLAlchemy
    cycle = relationship("TCycle", back_populates="classes")
    niveau = relationship("TNiveau", back_populates="classes")
    annee_scolaire = relationship("TAnneeScolaire", back_populates="classes")

    def __repr__(self):
        return f"<TClasse(ID={self.IDTClasse}, Libelle='{self.LibClasse}', Capacite={self.Capacite})>"
