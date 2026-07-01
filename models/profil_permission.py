from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.database import Base


class ProfilPermission(Base):
    __tablename__ = "ProfilPermission"

    IDProfil = Column(Integer, ForeignKey("Profil.IDProfil", ondelete="CASCADE"), primary_key=True)
    IDPermission = Column(Integer, ForeignKey("Permission.IDPermission", ondelete="CASCADE"), primary_key=True)
    Accordee = Column(Boolean, default=False, nullable=False)
