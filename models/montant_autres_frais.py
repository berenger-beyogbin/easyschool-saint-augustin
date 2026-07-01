from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class MontantAutresFrais(Base):
    """
    Montant des autres frais associes a un niveau, une annee scolaire, type de frais et etablissement.
    """
    __tablename__ = "MontantAutresFrais"

    __table_args__ = (
        UniqueConstraint("IDAnneeScolaire", "IDT_Niveau", "IDAutres_Frais", "IDEtablissement_Ecole", name="uq_montant_autres_unique"),
    )

    IDMontantAutres = Column(Integer, primary_key=True, autoincrement=True)
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDEtablissement_Ecole = Column(Integer, ForeignKey("Etablissement_Ecole.IDEtablissement_Ecole", ondelete="CASCADE"), nullable=True)
    MontantFrais = Column(Numeric(12, 2), nullable=False, default=0.0)
    IDT_Niveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="CASCADE"), nullable=False)
    IDAutres_Frais = Column(Integer, ForeignKey("Autres_Frais.IDAutres_Frais", ondelete="CASCADE"), nullable=False)
    KeyCompose = Column(String(50), nullable=True)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    etablissement = relationship("EtablissementEcole")
    niveau = relationship("TNiveau")
    autre_frais = relationship("AutresFrais")

    def __repr__(self):
        return f"<MontantAutresFrais(ID={self.IDMontantAutres}, Montant={self.MontantFrais})>"
