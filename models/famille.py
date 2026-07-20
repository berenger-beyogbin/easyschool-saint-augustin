from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class TFamille(Base):
    """
    Modèle de données pour la table TFamille (gestion des parents / responsables légaux).
    """
    __tablename__ = "TFamille"

    __table_args__ = (
        UniqueConstraint("NomResponsable", "CellulaireResponsable", name="uq_famille_nom_cellulaire"),
    )

    IdTFamille = Column(Integer, primary_key=True, autoincrement=True)
    
    # Responsable legal principal
    NomResponsable = Column(String(50), nullable=False)
    QualiteResponsable = Column(Integer, nullable=False) # 1=Tuteur, 2=Pere, 3=Mere par exemple
    ProfessionResponsable = Column(String(25), nullable=True)
    TypeResponsable = Column(Integer, nullable=True)
    NumeroPieceIdentite = Column(String(25), nullable=True)
    AdresseResponsable = Column(String(25), nullable=True)
    CellulaireResponsable = Column(String(25), nullable=False) # Téléphone responsable obligatoire
    EmailResponsable = Column(String(40), nullable=True)
    
    # Statuts specifiques
    SIMaitre = Column(Boolean, default=False)
    EbrieAbobote = Column(Boolean, default=False)
    
    # Personne a contacter en cas d'urgence
    NomUrgence = Column(String(50), nullable=True)
    ContactUrgence = Column(String(50), nullable=True)
    HabitationUrgence = Column(String(50), nullable=True)
    UrgenceMoimeme = Column(Boolean, default=False)
    
    # Localisation generale de la famille
    HabitationParent = Column(String(50), nullable=True)
    
    # Pere de l'eleve
    NomPere = Column(String(50), nullable=True)
    ProfessionPere = Column(String(25), nullable=True)
    TelPere = Column(String(25), nullable=True)
    
    # Mere de l'eleve
    NomMere = Column(String(50), nullable=True)
    ProfessionMere = Column(String(25), nullable=True)
    TelMere = Column(String(25), nullable=True)
    
    # Autres indicateurs
    EnsCatPrimaire = Column(Boolean, default=False)
    EnsCatSecondaire = Column(Boolean, default=False)

    # Relations — cascade limitée volontairement pour éviter les suppressions en masse
    # delete-orphan retiré : la suppression d'une famille ne doit pas supprimer automatiquement les élèves.
    # La protection est assurée au niveau service (FamilleService.delete_famille vérifie les élèves liés).
    eleves = relationship("Eleve", back_populates="famille", cascade="save-update, merge")
    inscriptions = relationship("TInscription", back_populates="famille", cascade="save-update, merge")

    def __repr__(self):
        return f"<TFamille(ID={self.IdTFamille}, Responsable='{self.NomResponsable}')>"
