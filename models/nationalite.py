from sqlalchemy import Column, Integer, String
from app.database import Base

class TNationalite(Base):
    """
    Table des Nationalites pour les fiches d'eleves ou d'enseignants.
    Mappe de la table HFSQL 'TNationalite'.
    """
    __tablename__ = "TNationalite"

    IDTNationalite = Column(Integer, primary_key=True, autoincrement=True)
    Nationalite = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<TNationalite(ID={self.IDTNationalite}, Libelle='{self.Nationalite}')>"
