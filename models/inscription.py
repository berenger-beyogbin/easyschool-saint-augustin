from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class TInscription(Base):
    """
    Modèle représentatif de la table TInscription pour lier les inscriptions d'élèves à une classe et une année scolaire.
    """
    __tablename__ = "TInscription"

    __table_args__ = (
        UniqueConstraint("IDEleve", "IDTAnneeScolaire", name="uq_inscription_eleve_annee"),
    )

    IDTInscription = Column(Integer, primary_key=True, autoincrement=True)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="CASCADE"), nullable=False)
    IDFamille = Column(Integer, ForeignKey("TFamille.IdTFamille", ondelete="CASCADE"), nullable=False)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="CASCADE"), nullable=False)
    IDNiveau = Column(Integer, ForeignKey("TNiveau.IDT_Niveau", ondelete="CASCADE"), nullable=False)
    IDClasse = Column(Integer, ForeignKey("TClasse.IDTClasse", ondelete="CASCADE"), nullable=False)
    
    # Options d'inscription
    Nouveau = Column(Boolean, default=True)
    Scolarite = Column(Boolean, default=True)
    Transport = Column(Boolean, default=False)
    Cantine = Column(Boolean, default=False)
    AutresFrais = Column(Boolean, default=False)
    
    # Audit
    Login = Column(String(50), nullable=True)
    DateInscription = Column(Date, nullable=False)

    # Statut d'affectation de l'État (AFFECTE_ETAT / NON_AFFECTE_ETAT)
    StatutAffectation = Column(String(20), nullable=False, default="AFFECTE_ETAT")

    # Relations
    annee_scolaire = relationship("TAnneeScolaire")
    famille = relationship("TFamille", back_populates="inscriptions")
    eleve = relationship("Eleve", back_populates="inscriptions")
    niveau = relationship("TNiveau")
    classe = relationship("TClasse")

    def __repr__(self):
        return f"<TInscription(ID={self.IDTInscription}, EleveID={self.IDEleve}, ClasseID={self.IDClasse}, AnneeID={self.IDTAnneeScolaire})>"
