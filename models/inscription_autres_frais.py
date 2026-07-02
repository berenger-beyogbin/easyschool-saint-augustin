from datetime import date
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class InscriptionAutresFrais(Base):
    """
    Fige les autres frais coches a l'inscription d'un eleve (snapshot du montant et du libelle).
    """
    __tablename__ = "InscriptionAutresFrais"

    __table_args__ = (
        UniqueConstraint("IDTInscription", "IDAutres_Frais", name="uq_inscription_autres_frais_unique"),
    )

    IDInscriptionAutresFrais = Column(Integer, primary_key=True, autoincrement=True)
    IDTInscription = Column(Integer, ForeignKey("TInscription.IDTInscription", ondelete="CASCADE"), nullable=False)
    IDAutres_Frais = Column(Integer, ForeignKey("Autres_Frais.IDAutres_Frais", ondelete="RESTRICT"), nullable=False)
    IDMontantAutres = Column(Integer, ForeignKey("MontantAutresFrais.IDMontantAutres", ondelete="SET NULL"), nullable=True)
    MontantApplique = Column(Numeric(12, 2), nullable=False, default=0)
    Obligatoire = Column(Boolean, nullable=False, default=False)
    DateCreation = Column(Date, nullable=False, default=date.today)
    Login = Column(String(50), nullable=True)
    LibelleSnapshot = Column(String(50), nullable=True)
    CodeFraisSnapshot = Column(String(10), nullable=True)

    # Relations
    inscription = relationship("TInscription")
    autre_frais = relationship("AutresFrais")
    montant_autres = relationship("MontantAutresFrais")

    def __repr__(self):
        return f"<InscriptionAutresFrais(ID={self.IDInscriptionAutresFrais}, Inscription={self.IDTInscription}, Frais={self.IDAutres_Frais}, Montant={self.MontantApplique})>"
