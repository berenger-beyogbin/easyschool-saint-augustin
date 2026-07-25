from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Time, Numeric, Boolean, Text,
    ForeignKey, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Vente(Base):
    """
    Entete d'une vente kiosque (un panier valide = une Vente + ses VenteLigne).
    Remplace StockSortie comme registre des ventes (D2) : StockSortie est
    conservee en base pour l'historique anterieur a cette migration, mais
    n'est plus alimentee.
    """
    __tablename__ = "Vente"

    __table_args__ = (
        CheckConstraint('"MontantTotal" >= 0', name="ck_vente_montant_total_positif"),
        UniqueConstraint("NumeroRecu", name="uq_vente_numero_recu"),
    )

    IDVente = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : une vente est une piece financiere et un historique,
    # elle ne doit pas disparaitre avec l'annee scolaire (meme politique que
    # StockSortie/VersementScol, audit P0-02).
    IDTAnneeScolaire = Column(Integer, ForeignKey("TAnneeScolaire.IDTAnneeScolaire", ondelete="RESTRICT"), nullable=False)
    NumeroRecu = Column(String(20), nullable=False)
    DateVente = Column(Date, nullable=False)
    HeureVente = Column(Time, nullable=False)
    ModePaiement = Column(String(30), nullable=False, default="Espèce")
    MontantTotal = Column(Numeric(12, 2), nullable=False)
    Login = Column(String(50), nullable=True)

    # Annulation tracee (meme motif que VersementScol/SortieFin, B7) : une
    # vente enregistree n'est jamais supprimee physiquement, elle est marquee
    # annulee (piste d'audit conservee, exclue des agregations financieres).
    Annule = Column(Boolean, nullable=False, default=False)
    AnnulePar = Column(String(50), nullable=True)
    DateAnnulation = Column(DateTime, nullable=True)
    MotifAnnulation = Column(Text, nullable=True)

    annee_scolaire = relationship("TAnneeScolaire")
    lignes = relationship("VenteLigne", back_populates="vente", order_by="VenteLigne.IDVenteLigne")

    def __repr__(self):
        return f"<Vente(ID={self.IDVente}, NumeroRecu={self.NumeroRecu}, Total={self.MontantTotal})>"


class VenteLigne(Base):
    """Ligne d'article d'une vente (une par article/KIT du panier)."""
    __tablename__ = "VenteLigne"

    __table_args__ = (
        CheckConstraint('"Quantite" > 0', name="ck_vente_ligne_quantite_positive"),
    )

    IDVenteLigne = Column(Integer, primary_key=True, autoincrement=True)
    # ON DELETE RESTRICT : une vente n'est jamais supprimee (seulement
    # annulee), donc ses lignes non plus.
    IDVente = Column(Integer, ForeignKey("Vente.IDVente", ondelete="RESTRICT"), nullable=False)
    IDTArticle = Column(Integer, ForeignKey("TArticle.IDTArticle", ondelete="RESTRICT"), nullable=False)
    Quantite = Column(Integer, nullable=False)
    PrixUnitaire = Column(Numeric(12, 2), nullable=False)
    Total = Column(Numeric(12, 2), nullable=False)

    vente = relationship("Vente", back_populates="lignes")
    article = relationship("Article")

    def __repr__(self):
        return f"<VenteLigne(ID={self.IDVenteLigne}, IDVente={self.IDVente}, IDTArticle={self.IDTArticle}, Qte={self.Quantite})>"
