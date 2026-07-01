from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Eleve(Base):
    """
    Modèle de données pour la table Eleve.
    """
    __tablename__ = "Eleve"

    IDEleve = Column(Integer, primary_key=True, autoincrement=True)
    Matricule = Column(String(50), nullable=False, unique=True)
    Nom = Column(String(35), nullable=False)
    Prenoms = Column(String(75), nullable=False)
    DateNaissance = Column(Date, nullable=False)
    LieuNaissance = Column(String(30), nullable=True)
    Sexe = Column(Integer, nullable=False) # 1 = Masculin, 2 = Féminin
    
    # Cles etrangeres
    IDNationalite = Column(Integer, ForeignKey("TNationalite.IDTNationalite", ondelete="SET NULL"), nullable=True)
    IDReligion = Column(Integer, ForeignKey("TReligion.IDTReligion", ondelete="SET NULL"), nullable=True)
    IDFamille = Column(Integer, ForeignKey("TFamille.IdTFamille", ondelete="SET NULL"), nullable=True)
    
    # Photo et administratifs
    PhotoPath = Column(String(255), nullable=True) # Enregistre dans assets/photos_eleves/
    NumExtrait = Column(String(20), nullable=True)
    DateExtrait = Column(Date, nullable=True)
    LieuDelivrance = Column(String(30), nullable=True)
    Habitation = Column(String(25), nullable=True)
    
    # Urgence
    NomUrgence = Column(String(50), nullable=True)
    ContactUrgence = Column(String(50), nullable=True)
    HabitationUrgence = Column(String(50), nullable=True)

    # Relations
    famille = relationship("TFamille", back_populates="eleves")
    nationalite = relationship("TNationalite")
    religion = relationship("TReligion")
    # cascade limitée : delete-orphan retiré pour éviter la suppression automatique d'inscriptions.
    # La protection est assurée par EleveService.delete_eleve (vérifie inscriptions et versements).
    inscriptions = relationship("TInscription", back_populates="eleve", cascade="save-update, merge")

    def __repr__(self):
        return f"<Eleve(ID={self.IDEleve}, Matricule='{self.Matricule}', Nom='{self.Nom}', Prenoms='{self.Prenoms}')>"
