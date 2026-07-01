from sqlalchemy import Column, Integer, String
from app.database import Base

class Compte(Base):
    """
    Table Compte pour la gestion des comptes de comptabilite.
    """
    __tablename__ = "Compte"

    IDCompte = Column(Integer, primary_key=True, autoincrement=True)
    NumCompte = Column(String(50), nullable=False, unique=True)
    LibCompte = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Compte(ID={self.IDCompte}, Num='{self.NumCompte}', Lib='{self.LibCompte}')>"
