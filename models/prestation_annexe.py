from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from utils.datetime_utils import utcnow


class PrestationAnnexe(Base):
    """
    Prestation annexe incluse dans les frais de scolarité (Anglais/Informatique,
    Entrepreneuriat, Musique, etc.). Ventilée analytiquement à partir des paiements de scolarité,
    par ordre de priorité correspondant à l'ordre de création (IDPrestation croissant).
    """
    __tablename__ = "PrestationAnnexe"

    IDPrestation = Column(Integer, primary_key=True, autoincrement=True)
    Code = Column(String(50), nullable=False, unique=True)
    Libelle = Column(String(200), nullable=False)
    MontantAnnuel = Column(Numeric(12, 2), nullable=False, default=0.0)
    IDPrestataire = Column(Integer, ForeignKey("Prestataire.IDPrestataire", ondelete="SET NULL"), nullable=True)
    IsActive = Column(Boolean, default=True, nullable=False)
    CreatedAt = Column(DateTime, default=utcnow)
    UpdatedAt = Column(DateTime, default=utcnow, onupdate=utcnow)

    prestataire = relationship("Prestataire", back_populates="prestations")
    ventilations = relationship("VentilationPrestation", back_populates="prestation", cascade="all, delete-orphan")
    tarifs_niveau = relationship("PrestationTarifNiveau", back_populates="prestation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PrestationAnnexe(ID={self.IDPrestation}, Code={self.Code}, Montant={self.MontantAnnuel})>"
