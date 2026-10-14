"""hachage et vérification des mot de passe en utilisant Argon 2"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

LONGUEUR_MINIMALE = 12

_hasher = PasswordHasher()


def valider_mot_de_passe(mot_de_passe: str) -> None:
    """Lève ValueError si le mot de passe est trop faible."""
    if len(mot_de_passe) < LONGUEUR_MINIMALE:
        raise ValueError(
            f"Le mot de passe doit contenir au moins {LONGUEUR_MINIMALE} caractères."
        )


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Retourne l'empreinte Argon2 du mot de passe, sel inclus."""
    return _hasher.hash(mot_de_passe)


def verifier_mot_de_passe(empreinte: str, mot_de_passe: str) -> bool:
    """Retourne True si le mot de passe correspond à l'empreinte."""
    try:
        return _hasher.verify(empreinte, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False
