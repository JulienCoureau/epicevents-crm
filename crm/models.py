from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe mère de tous les modèles ; elle tient la liste des tables à créer."""


class Role(Base):
    """Département d'un collaborateur : commercial, support ou gestion."""

    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(20), unique=True)

    def __repr__(self) -> str:
        return f"Role(id={self.id}, nom={self.nom!r})"
