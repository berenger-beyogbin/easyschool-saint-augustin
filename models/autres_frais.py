from sqlalchemy import Column, Integer, String
from app.database import Base

class AutresFrais(Base):
    """
    Table representant les types d'autres frais (Ex: Tenue, T-shirt, Macaron, Assurance).
    Mappe de la table HFSQL 'Autres_Frais'.
    """
    __tablename__ = "Autres_Frais"

    IDAutres_Frais = Column(Integer, primary_key=True, autoincrement=True)
    CodeFrais = Column(String(10), unique=True, nullable=False)
    LibelleFrais = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<AutresFrais(ID={self.IDAutres_Frais}, Code='{self.CodeFrais}', Libelle='{self.LibelleFrais}')>"
