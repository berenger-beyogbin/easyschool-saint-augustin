from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from utils.datetime_utils import utcnow


class VentilationPrestation(Base):
    """
    Table de ventilation analytique : trace les montants de chaque prestation annexe
    considérés comme couverts par les paiements de scolarité d'un élève.
    Calculé par affectation en cascade : chaque prestation est couverte intégralement,
    dans l'ordre de création des prestations, avant de passer à la suivante.
    """
    __tablename__ = "VentilationPrestation"

    __table_args__ = (
        UniqueConstraint(
            "IDEleve", "IDPrestation", "IDAnneeScolaire",
            name="uq_ventilation_eleve_prestation_annee"
        ),
    )

    IDVentilation = Column(Integer, primary_key=True, autoincrement=True)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="CASCADE"), nullable=False)
    IDPrestation = Column(Integer, ForeignKey("PrestationAnnexe.IDPrestation", ondelete="CASCADE"), nullable=False)
    IDAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    MontantVentile = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantTheorique = Column(Numeric(12, 2), nullable=False, default=0.0)
    TauxPaiement = Column(Numeric(6, 4), nullable=False, default=0.0)
    ModeCalcul = Column(String(20), nullable=False, default="CASCADE")
    CalculeAt = Column(DateTime, default=utcnow, onupdate=utcnow)
    CreatedAt = Column(DateTime, default=utcnow)
    UpdatedAt = Column(DateTime, default=utcnow, onupdate=utcnow)

    eleve = relationship("Eleve")
    prestation = relationship("PrestationAnnexe", back_populates="ventilations")
    annee_scolaire = relationship("TAnneeScolaire")

    def __repr__(self):
        return (
            f"<VentilationPrestation(Eleve={self.IDEleve}, "
            f"Prestation={self.IDPrestation}, Ventile={self.MontantVentile})>"
        )
