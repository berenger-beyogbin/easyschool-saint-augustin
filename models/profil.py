from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class Profil(Base):
    __tablename__ = "Profil"

    IDProfil = Column(Integer, primary_key=True, autoincrement=True)
    Code = Column(String(20), unique=True, nullable=False)
    Libelle = Column(String(100), nullable=False)
    Description = Column(String(255))
    IsAdmin = Column(Boolean, default=False, nullable=False)
    IsActive = Column(Boolean, default=True, nullable=False)
    DateCreation = Column(DateTime, default=func.now())
