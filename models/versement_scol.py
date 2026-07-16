from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import relationship
from app.database import Base

class VersementScol(Base):
    """
    Represente la table des versements de scolarite, cantine, transport, etc.
    Mappe de la table HFSQL 'VersementScol'.
    """
    __tablename__ = "VersementScol"

    __table_args__ = (
        CheckConstraint("\"MontantVersTrans\" >= 0", name="ck_versement_scol_trans_positif"),
        CheckConstraint("\"MontantVersSco\" >= 0", name="ck_versement_scol_sco_positif"),
        CheckConstraint("\"MontantCantine\" >= 0", name="ck_versement_scol_cantine_positif"),
        CheckConstraint("\"MontantVersAutres\" >= 0", name="ck_versement_scol_autres_positif"),
    )

    IDVersementScol = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : un versement est une piece financiere, sa disparition
    # ne doit jamais etre un effet de bord de la suppression d'une famille,
    # d'une annee ou d'un eleve.
    IDFamille = Column(Integer, ForeignKey("TFamille.IdTFamille", ondelete="RESTRICT"), nullable=False)
    DateVers = Column(Date, nullable=False)
    MontantVersTrans = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantVersSco = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantCantine = Column(Numeric(12, 2), nullable=False, default=0.0)
    MontantVersAutres = Column(Numeric(12, 2), nullable=False, default=0.0)
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    IDEleve = Column(Integer, ForeignKey("Eleve.IDEleve", ondelete="RESTRICT"), nullable=False)
    Restitution = Column(Boolean, default=False)
    Login = Column(String(50), nullable=True)
    Reduction = Column(Boolean, default=False)
    Impaye = Column(Boolean, default=False)

    # Annulation tracee : un versement enregistre n'est jamais supprime
    # physiquement, il est marque annule (piste d'audit conservee, exclu des
    # agregations financieres).
    Annule = Column(Boolean, nullable=False, default=False)
    AnnulePar = Column(String(50), nullable=True)
    DateAnnulation = Column(DateTime, nullable=True)
    MotifAnnulation = Column(Text, nullable=True)

    # Relations
    famille = relationship("TFamille")
    eleve = relationship("Eleve")
    annee_scolaire = relationship("TAnneeScolaire")

    def __repr__(self):
        return f"<VersementScol(ID={self.IDVersementScol}, Eleve={self.IDEleve}, Scol={self.MontantVersSco}, Trans={self.MontantVersTrans}, Cant={self.MontantCantine})>"
