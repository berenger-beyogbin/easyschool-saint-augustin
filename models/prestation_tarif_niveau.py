from sqlalchemy import Column, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class PrestationTarifNiveau(Base):
    """
    Surcharge du montant annuel d'une PrestationAnnexe pour un niveau donne,
    sur une annee scolaire donnee. En l'absence de surcharge, le moteur de
    ventilation utilise PrestationAnnexe.MontantAnnuel.
    """
    __tablename__ = "PrestationTarifNiveau"

    __table_args__ = (
        UniqueConstraint("IDAnneeScolaire", "IDT_Niveau", "IDPrestation", name="uq_prestation_tarif_annee_niveau"),
    )

    IDPrestationTarif = Column(Integer, primary_key=True, autoincrement=True)
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDT_Niveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="CASCADE"), nullable=False)
    IDPrestation = Column(Integer, ForeignKey("PrestationAnnexe.IDPrestation", ondelete="CASCADE"), nullable=False)
    MontantAnnuel = Column(Numeric(12, 2), nullable=False, default=0.0)

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    niveau = relationship("TNiveau")
    prestation = relationship("PrestationAnnexe", back_populates="tarifs_niveau")

    def __repr__(self):
        return f"<PrestationTarifNiveau(ID={self.IDPrestationTarif}, Prestation={self.IDPrestation}, Niveau={self.IDT_Niveau}, Montant={self.MontantAnnuel})>"
