from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VersementScol(Base):
    """
    Represente la table des versements de scolarite, cantine, transport, etc.
    Mappe de la table HFSQL 'VersementScol'.
    """
    __tablename__ = "VersementScol"

    IDVersementScol = Column(Integer, primary_key=True, autoincrement=True)
    IDFamille = Column(Integer, ForeignKey("TFamille.IdTFamille", ondelete="CASCADE"), nullable=False)
    DateVers = Column(Date, nullable=False)
    MontantVersTrans = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantVersSco = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantCantine = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantVersAutres = Column(Numeric(12, 2), nullable=False, default=0.0)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="CASCADE"), nullable=False)
    Restitution = Column(Boolean, default=False)
    Login = Column(String(50), nullable=True)
    Reduction = Column(Boolean, default=False)
    Impaye = Column(Boolean, default=False)

    # Relations
    famille = relationship("TFamille")
    eleve = relationship("Eleve")
    annee_scolaire = relationship("TAnneeScolaire")

    def __repr__(self):
        return f"<VersementScol(ID={self.IDVersementScol}, Eleve={self.IDEleve}, Scol={self.MontantVersSco}, Trans={self.MontantVersTrans}, Cant={self.MontantCantine})>"
