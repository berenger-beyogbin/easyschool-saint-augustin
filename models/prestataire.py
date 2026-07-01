from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Prestataire(Base):
    """Prestataire extérieur assurant une ou plusieurs prestations annexes incluses dans la scolarité."""
    __tablename__ = "Prestataire"

    IDPrestataire = Column(Integer, primary_key=True, autoincrement=True)
    Nom = Column(String(200), nullable=False)
    Contact = Column(String(100), nullable=True)
    Telephone = Column(String(50), nullable=True)
    Email = Column(String(150), nullable=True)
    IsActive = Column(Boolean, default=True, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prestations = relationship("PrestationAnnexe", back_populates="prestataire")

    def __repr__(self):
        return f"<Prestataire(ID={self.IDPrestataire}, Nom={self.Nom})>"
