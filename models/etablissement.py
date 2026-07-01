from sqlalchemy import Column, Integer, String, Boolean, LargeBinary
from app.database import Base

class EtablissementEcole(Base):
    """
    Represente l'ecole ou l'etablissement d'enseignement.
    Mappe direct de la table HFSQL 'Etablissement_Ecole' vers PostgreSQL.
    """
    __tablename__ = "Etablissement_Ecole"

    IDEtablissement_Ecole = Column(Integer, primary_key=True, autoincrement=True)
    RaisonSociale = Column(String(100), nullable=False) # Nom de l'etablissement
    Sigle = Column(String(50))
    Adresse = Column(String(50))
    Localite = Column(String(170))
    Telephone = Column(String(50))
    Email = Column(String(100))
    LogoPath = Column(String(255), nullable=True) # Pour stocker le chemin relatif du logo
    CODEcole = Column(String(10), nullable=True)
    Dren = Column(String(100)) # Direction Regionale de l'Education Nationale
    IEP = Column(String(100)) # Inspection de l'Enseignement Primaire
    Statut = Column(Boolean, default=True) # Actif / Inactif
    ChefEtab = Column(String(150)) # Nom du Chef d'etablissement
    Ministere = Column(String(200))
    Slogan = Column(String(100))
    CodeEtab = Column(String(10))
    TypeEtab = Column(String(50)) # Type d'enseignement (Ex: Primaire, Secondaire)

    def __repr__(self):
        return f"<EtablissementEcole(ID={self.IDEtablissement_Ecole}, Nom='{self.RaisonSociale}')>"
