from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class TAnneeScolaire(Base):
    """
    Table des annees scolaires (Ex: 2026-2027).
    Mappe de la table HFSQL 'TAnneeScolaire'.
    """
    __tablename__ = "TAnneeScolaire"

    IDTAnneeScolaire = Column(Integer, primary_key=True, autoincrement=True)
    Libelle = Column(String(12), nullable=False, unique=True) # Ex: "2026-2027"
    Cloturer = Column(Boolean, default=False) # True si l'annee est close

    # Relations avec les autres tables
    niveaux = relationship("TNiveau", back_populates="annee_scolaire")
    classes = relationship("TClasse", back_populates="annee_scolaire")

    def __repr__(self):
        etat = "Cloturee" if self.Cloturer else "Active"
        return f"<TAnneeScolaire(ID={self.IDTAnneeScolaire}, Libelle='{self.Libelle}', Etat='{etat}')>"
