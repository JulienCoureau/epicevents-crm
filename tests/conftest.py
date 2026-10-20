import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from crm import auth
from crm.models import Base, Role

SECRET_DE_TEST = "secret-de-test-uniquement-pour-pytest-0123456789"


@pytest.fixture(autouse=True)
def environnement_isole(monkeypatch, tmp_path):
    """Remplace le secret JWT et le fichier jeton, pour chaque test."""
    monkeypatch.setenv("JWT_SECRET", SECRET_DE_TEST)
    monkeypatch.setattr(auth, "FICHIER_JETON", tmp_path / "jeton")


@pytest.fixture
def session():
    """Session sur une base vide qui contient seulement les trois rôles."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([Role(nom=nom) for nom in ("commercial", "support", "gestion")])
        session.commit()
        yield session
    engine.dispose()
