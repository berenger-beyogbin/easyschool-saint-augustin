from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    """
    Journal d'audit des actions sensibles (annulations financieres, suppressions,
    etc.). Contrairement au champ Login (chaine de caracteres non fiable), relie
    l'auteur a un IDUtilisateur reel via cle etrangere.
    """
    __tablename__ = "AuditLog"

    IDAuditLog = Column(Integer, primary_key=True, autoincrement=True)
    # SET NULL : un utilisateur supprime ne doit pas effacer l'historique de ses actions.
    IDUtilisateur = Column(Integer, ForeignKey("Utilisateur.IDUtilisateur", ondelete="SET NULL"), nullable=True)
    Action = Column(String(50), nullable=False)          # ex: "ANNULER_VERSEMENT", "ANNULER_MOUVEMENT"
    TableCible = Column(String(50), nullable=False)      # ex: "VersementScol"
    IDCible = Column(Integer, nullable=False)            # PK de l'enregistrement concerne
    AncienneValeur = Column(Text, nullable=True)
    NouvelleValeur = Column(Text, nullable=True)
    Motif = Column(Text, nullable=True)
    DateAction = Column(DateTime, nullable=False, default=datetime.now)

    # Relation
    utilisateur = relationship("Utilisateur")

    def __repr__(self):
        return f"<AuditLog(ID={self.IDAuditLog}, Action='{self.Action}', Table='{self.TableCible}', Cible={self.IDCible})>"
