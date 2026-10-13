"""Creation des tables de la base et insertion des 3 rôles
→ utilise le compte administrateur
→ on le lance une fois a l'instalation"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from crm.config import database_url
from crm.models import Base, Role

ROLES = ("commercial", "support", "gestion")


def main() -> None:
    """Crée les tables manquantes, puis ajoute les rôles absents."""
    engine = create_engine(database_url(admin=True))
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        existants = set(session.scalars(select(Role.nom)))
        for nom in ROLES:
            if nom not in existants:
                session.add(Role(nom=nom))
        session.commit()

    print("Tables créées et rôles en place.")


if __name__ == "__main__":
    main()
