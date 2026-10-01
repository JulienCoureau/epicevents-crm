import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()  # lit le fichier .env et place son contenu dans os.environ


def _require(name: str) -> str:
    """Retourne la variable d'environnement, ou échoue clairement si elle manque."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name}")
    return value


def database_url(admin: bool = False) -> URL:
    """Construit l'URL de connexion.

    admin=False : compte applicatif (usage quotidien, droits limités).
    admin=True  : compte propriétaire, réservé à la création des tables.
    """
    prefix = "DB_ADMIN" if admin else "DB_APP"
    return URL.create(
        drivername="postgresql+psycopg",
        username=_require(f"{prefix}_USER"),
        password=_require(f"{prefix}_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=_require("DB_NAME"),
    )
