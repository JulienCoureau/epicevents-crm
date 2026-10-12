"""Modèles de données : une classe par table du schéma (docs/schema-bdd.md)."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Numeric,
    ForeignKey,
    String,
    DateTime,
    func,
    Text,
)
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
    evenements: Mapped[list["Evenement"]] = relationship(back_populates="support")

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
    contrats: Mapped[list["Contrat"]] = relationship(back_populates="client")

    def __repr__(self) -> str:
        return f"Client(id={self.id}, nom_complet={self.nom_complet!r})"


class Contrat(Base):
    """Contrat passé avec un client"""

    __tablename__ = "contrat"
    __table_args__ = (
        CheckConstraint("montant_total >= 0", name="montant_total_positif"),
        CheckConstraint(
            "montant_restant >= 0 AND montant_restant <= montant_total",
            name="montant_restant_valide",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"))
    montant_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    montant_restant: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    date_creation: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    signe: Mapped[bool] = mapped_column(Boolean, default=False)

    client: Mapped["Client"] = relationship(back_populates="contrats")
    evenement: Mapped["Evenement | None"] = relationship(back_populates="contrat")

    def __repr__(self) -> str:
        return f"Contrat(id={self.id}, signe={self.signe})"


class Evenement(Base):
    """Événement organisé pour un contrat signé, suivi par un collaborateur"""

    __tablename__ = "evenement"
    __table_args__ = (
        CheckConstraint("date_fin > date_debut", name="dates_coherentes"),
        CheckConstraint("participants >= 0", name="participants_positif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    contrat_id: Mapped[int] = mapped_column(ForeignKey("contrat.id"), unique=True)
    support_id: Mapped[int | None] = mapped_column(ForeignKey("collaborateur.id"))
    date_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    date_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lieu: Mapped[str] = mapped_column(String(255))
    participants: Mapped[int]
    notes: Mapped[str | None] = mapped_column(Text)

    contrat: Mapped["Contrat"] = relationship(back_populates="evenement")
    support: Mapped["Collaborateur | None"] = relationship(back_populates="evenements")

    def __repr__(self) -> str:
        return f"Evenement(id={self.id}, nom={self.nom!r})"
