from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Utilisateur(Base):
    __tablename__ = "Utilisateur"

    IDUtilisateur = Column(Integer, primary_key=True, autoincrement=True)
    Login = Column(String(50), unique=True, nullable=False)
    MotDePasseHash = Column(String(255), nullable=False)
    Nom = Column(String(100), nullable=False)
    Prenoms = Column(String(150))
    Email = Column(String(150))
    IDProfil = Column(Integer, ForeignKey("Profil.IDProfil"), nullable=False)
    IsActive = Column(Boolean, default=True, nullable=False)
    DateCreation = Column(DateTime, default=func.now())
    DernierAcces = Column(DateTime)
    ImprimanteDefaut = Column(String(255), nullable=True)

    profil = relationship("Profil", lazy="joined")
