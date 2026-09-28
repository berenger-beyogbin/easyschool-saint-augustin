from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CursusAnterieur(Base):
    """
    Ligne d'historique scolaire d'un eleve (fiche d'inscription CJGA,
    tableau "CURSUS SCOLAIRE" : annees / classe / moyenne annuelle /
    etablissement). Purement descriptif, saisi a l'inscription.
    """
    __tablename__ = "CursusAnterieur"

    IDCursusAnterieur = Column(Integer, primary_key=True, autoincrement=True)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="CASCADE"), nullable=False)
    AnneeScolaire = Column(String(20), nullable=True)   # ex: "2023/2024"
    Classe = Column(String(30), nullable=True)
    MoyenneAnnuelle = Column(Numeric(5, 2), nullable=True)
    Etablissement = Column(String(100), nullable=True)

    eleve = relationship("Eleve", back_populates="cursus_anterieur")

    def __repr__(self):
        return f"<CursusAnterieur(Eleve={self.IDEleve}, Annee='{self.AnneeScolaire}', Classe='{self.Classe}')>"
