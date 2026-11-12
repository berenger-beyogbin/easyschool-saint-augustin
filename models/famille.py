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
    TelBureauResponsable = Column(String(25), nullable=True)
    TelDomicileResponsable = Column(String(25), nullable=True)

    # Statuts specifiques
    SIMaitre = Column(Boolean, default=False)
    EbrieAbobote = Column(Boolean, default=False)

    # Personne a contacter en cas d'urgence
    NomUrgence = Column(String(50), nullable=True)
    ContactUrgence = Column(String(20), nullable=True)
    HabitationUrgence = Column(String(50), nullable=True)
    UrgenceMoimeme = Column(Boolean, default=False)

    # Localisation generale de la famille
    HabitationParent = Column(String(50), nullable=True)

    # Pere de l'eleve
    NomPere = Column(String(50), nullable=True)
    ProfessionPere = Column(String(25), nullable=True)
    TelPere = Column(String(25), nullable=True)
    EmailPere = Column(String(80), nullable=True)
    EntreprisePere = Column(String(40), nullable=True)
    LieuResidencePere = Column(String(50), nullable=True)
    TelBureauPere = Column(String(25), nullable=True)
    TelDomicilePere = Column(String(25), nullable=True)
    AdressePostalePere = Column(String(50), nullable=True)

    # Mere de l'eleve
    NomMere = Column(String(50), nullable=True)
    ProfessionMere = Column(String(25), nullable=True)
    TelMere = Column(String(25), nullable=True)
    EmailMere = Column(String(80), nullable=True)
    EntrepriseMere = Column(String(40), nullable=True)
    LieuResidenceMere = Column(String(50), nullable=True)
    TelBureauMere = Column(String(25), nullable=True)
    TelDomicileMere = Column(String(25), nullable=True)
    AdressePostaleMere = Column(String(50), nullable=True)

    # Tuteur (distinct du responsable legal : peut etre une tierce personne
    # non responsable au sens administratif, cf. bloc TUTEUR de la fiche CJGA)
    NomTuteur = Column(String(50), nullable=True)
    ProfessionTuteur = Column(String(25), nullable=True)
    EntrepriseTuteur = Column(String(40), nullable=True)
    CelTuteur = Column(String(25), nullable=True)
    EmailTuteur = Column(String(80), nullable=True)
    TelBureauTuteur = Column(String(25), nullable=True)
    TelDomicileTuteur = Column(String(25), nullable=True)
    AdressePostaleTuteur = Column(String(50), nullable=True)

    # Notes libres du dossier d'inscription
    MotivationChoixEcole = Column(String(255), nullable=True)
    Observations = Column(String(500), nullable=True)

    # Relations — cascade limitée volontairement pour éviter les suppressions en masse
    # delete-orphan retiré : la suppression d'une famille ne doit pas supprimer automatiquement les élèves.
    # La protection est assurée au niveau service (FamilleService.delete_famille vérifie les élèves liés).
    eleves = relationship("Eleve", back_populates="famille", cascade="save-update, merge")
    inscriptions = relationship("TInscription", back_populates="famille", cascade="save-update, merge")

    def __repr__(self):
        return f"<TFamille(ID={self.IdTFamille}, Responsable='{self.NomResponsable}')>"
