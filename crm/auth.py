"""Authentification : vérification des identifiants et jeton JWT."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from crm.config import jwt_secret
from crm.models import Collaborateur
from crm.passwords import verifier_mot_de_passe

ALGORITHME = "HS256"
DUREE_JETON = timedelta(hours=8)
FICHIER_JETON = Path.home() / ".epicevents" / "jeton"


class AuthentificationError(Exception):
    """Levée quand l'utilisateur n'est pas, ou plus, authentifié."""


def authentifier(session: Session, email: str, mot_de_passe: str) -> Collaborateur:
    """Retourne le collaborateur si l'email et le mot de passe sont corrects."""
    collaborateur = session.scalars(
        select(Collaborateur).where(Collaborateur.email == email.strip().lower())
    ).one_or_none()
    if collaborateur is None or not verifier_mot_de_passe(
        collaborateur.mot_de_passe_hache, mot_de_passe
    ):
        raise AuthentificationError("Email ou mot de passe incorrect.")
    return collaborateur


def creer_jeton(collaborateur: Collaborateur) -> str:
    """Fabrique un jeton signé, valable DUREE_JETON."""
    maintenant = datetime.now(timezone.utc)
    contenu = {
        "sub": str(collaborateur.id),
        "iat": maintenant,
        "exp": maintenant + DUREE_JETON,
    }
    return jwt.encode(contenu, jwt_secret(), algorithm=ALGORITHME)


def enregistrer_jeton(jeton: str) -> None:
    """Écrit le jeton dans un fichier lisible par son seul propriétaire."""
    FICHIER_JETON.parent.mkdir(mode=0o700, exist_ok=True)
    FICHIER_JETON.touch(mode=0o600, exist_ok=True)
    FICHIER_JETON.chmod(0o600)
    FICHIER_JETON.write_text(jeton)


def supprimer_jeton() -> None:
    """Efface le jeton : c'est la déconnexion."""
    FICHIER_JETON.unlink(missing_ok=True)


def collaborateur_connecte(session: Session) -> Collaborateur:
    """Retourne le collaborateur désigné par le jeton, ou lève une erreur."""
    if not FICHIER_JETON.exists():
        raise AuthentificationError("Vous n'êtes pas connecté : lancez « login ».")
    try:
        contenu = jwt.decode(
            FICHIER_JETON.read_text(), jwt_secret(), algorithms=[ALGORITHME]
        )
    except jwt.ExpiredSignatureError:
        supprimer_jeton()
        raise AuthentificationError(
            "Session expirée : reconnectez-vous avec « login »."
        ) from None
    except jwt.InvalidTokenError:
        supprimer_jeton()
        raise AuthentificationError(
            "Jeton invalide : reconnectez-vous avec « login »."
        ) from None

    collaborateur = session.get(Collaborateur, int(contenu["sub"]))
    if collaborateur is None:
        supprimer_jeton()
        raise AuthentificationError("Compte introuvable : reconnectez-vous.")
    return collaborateur
