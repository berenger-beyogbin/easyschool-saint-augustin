from sqlalchemy import Column, Integer, String
from app.database import Base

class TReligion(Base):
    """
    Table des Religions.
    Mappe de la table HFSQL 'TReligion'.
    """
    __tablename__ = "TReligion"

    IDTReligion = Column(Integer, primary_key=True, autoincrement=True)
    Religion = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<TReligion(ID={self.IDTReligion}, Libelle='{self.Religion}')>"
