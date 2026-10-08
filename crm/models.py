"""Modèles de données : une classe par table du schéma (docs/schema-bdd.md)."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe mère de tous les modèles ; elle tient la liste des tables à créer."""


class Role(Base):
    """Département d'un collaborateur : commercial, support ou gestion."""

    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(20), unique=True)
    collaborateurs: Mapped[list["Collaborateur"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"Role(id={self.id}, nom={self.nom!r})"


class Collaborateur(Base):
    """Employé d'Epic Events, rattaché à un département (rôle)."""

    __tablename__ = "collaborateur"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_employe: Mapped[str] = mapped_column(String(20), unique=True)
    nom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))

    role: Mapped["Role"] = relationship(back_populates="collaborateurs")
    clients: Mapped[list["Client"]] = relationship(back_populates="commercial")

    def __repr__(self) -> str:
        return f"Collaborateur(id={self.id}, email={self.email!r})"


class Client(Base):
    """Client qui est suivi par un commercial"""

    __tablename__ = "client"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom_complet: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    telephone: Mapped[str | None] = mapped_column(String(30))
    entreprise: Mapped[str | None] = mapped_column(String(100))
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    derniere_mise_a_jour: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    commercial_id: Mapped[int] = mapped_column(ForeignKey("collaborateur.id"))

    commercial: Mapped["Collaborateur"] = relationship(back_populates="clients")

    def __repr__(self) -> str:
        return f"Client(id={self.id}, nom_complet={self.nom_complet!r})"
