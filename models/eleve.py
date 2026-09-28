from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Eleve(Base):
    """
    Modèle de données pour la table Eleve.
    """
    __tablename__ = "Eleve"
    __table_args__ = (
        UniqueConstraint("CodeExterne", name="uq_eleve_code_externe"),
    )

    IDEleve = Column(Integer, primary_key=True, autoincrement=True)
    Matricule = Column(String(50), nullable=False, unique=True)
    CodeExterne = Column(String(64), nullable=True)
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

    # Scolarite anterieure / dossier (fiche d'inscription CJGA, page 1)
    MatriculeNational = Column(String(30), nullable=True)
    EtablissementOrigine = Column(String(100), nullable=True)
    ClasseSuivieOrigine = Column(String(30), nullable=True)
    DeuxiemeLangue = Column(String(30), nullable=True)
    VitChezQui = Column(String(20), nullable=True) # PARENTS / PERE / MERE / TUTEUR

    # Renseignements religieux detailles
    Baptise = Column(Boolean, nullable=True)
    Confirme = Column(Boolean, nullable=True)
    ParoisseActuelle = Column(String(60), nullable=True)
    ActiviteParoisse = Column(String(100), nullable=True)
    PreciserEglise = Column(String(60), nullable=True)

    # Cadre reserve a la direction
    NDossier = Column(String(20), nullable=True)
    DateAdmission = Column(Date, nullable=True)
    AutorisationCourrier = Column(Boolean, nullable=True)

    # Documents a fournir (checklist du dossier d'inscription)
    DocExtraitNaissance = Column(Boolean, nullable=False, default=False)
    DocCertifScolarite = Column(Boolean, nullable=False, default=False)
    DocBulletins = Column(Boolean, nullable=False, default=False)
    DocPhotos = Column(Boolean, nullable=False, default=False)
    DocCarnetVaccination = Column(Boolean, nullable=False, default=False)
    DocCarnetSante = Column(Boolean, nullable=False, default=False)
    DocDispenseEPS = Column(Boolean, nullable=False, default=False)
    DocDispenseEPSCertificat = Column(Boolean, nullable=False, default=False)
    DocCarteSejour = Column(Boolean, nullable=False, default=False)
    DocLivretScolaire = Column(Boolean, nullable=False, default=False)

    # Renseignements medicaux — responsable(s) a prevenir en cas d'accident
    AccidentNom1 = Column(String(50), nullable=True)
    AccidentTel1 = Column(String(25), nullable=True)
    AccidentCel1 = Column(String(25), nullable=True)
    AccidentBureau1 = Column(String(25), nullable=True)
    AccidentNom2 = Column(String(50), nullable=True)
    AccidentTel2 = Column(String(25), nullable=True)
    AccidentCel2 = Column(String(25), nullable=True)
    AccidentBureau2 = Column(String(25), nullable=True)
    AccidentAdresse = Column(String(100), nullable=True)
    ConduireHopital = Column(Boolean, nullable=True)
    ConduireHopitalPrecision = Column(String(100), nullable=True)
    ConduireClinique = Column(Boolean, nullable=True)
    ConduireCliniquePrecision = Column(String(100), nullable=True)

    # Medecin traitant
    MedecinNom = Column(String(50), nullable=True)
    MedecinTel = Column(String(25), nullable=True)
    MedecinCel = Column(String(25), nullable=True)
    MedecinBureau = Column(String(25), nullable=True)
    MedecinAdresse = Column(String(100), nullable=True)

    # Informations medicales complementaires
    Maladie = Column(String(200), nullable=True)
    ContreIndications = Column(String(200), nullable=True)

    # Relations
    famille = relationship("TFamille", back_populates="eleves")
    nationalite = relationship("TNationalite")
    religion = relationship("TReligion")
    # cascade limitée : delete-orphan retiré pour éviter la suppression automatique d'inscriptions.
    # La protection est assurée par EleveService.delete_eleve (vérifie inscriptions et versements).
    inscriptions = relationship("TInscription", back_populates="eleve", cascade="save-update, merge")
    # Historique des etablissements/classes anterieurs (cursus scolaire) : purement
    # descriptif, pas de contrainte de retention comme pour inscriptions/versements.
    cursus_anterieur = relationship(
        "CursusAnterieur", back_populates="eleve",
        cascade="all, delete-orphan", order_by="CursusAnterieur.AnneeScolaire",
    )

    def __repr__(self):
        return f"<Eleve(ID={self.IDEleve}, Matricule='{self.Matricule}', Nom='{self.Nom}', Prenoms='{self.Prenoms}')>"
