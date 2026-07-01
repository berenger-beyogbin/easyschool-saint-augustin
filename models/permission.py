from sqlalchemy import Column, Integer, String
from app.database import Base


class Permission(Base):
    __tablename__ = "Permission"

    IDPermission = Column(Integer, primary_key=True, autoincrement=True)
    Code = Column(String(50), unique=True, nullable=False)
    Libelle = Column(String(100), nullable=False)
    Module = Column(String(50), nullable=False)
    Description = Column(String(255))
    Ordre = Column(Integer, default=0)
