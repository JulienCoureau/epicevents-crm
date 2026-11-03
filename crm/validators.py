"""Validation des données saisies : nettoyage et vérification avant écriture"""

import re

from crm.exceptions import DonneesInvalides

FORMAT_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FORMAT_TELEPHONE = re.compile(r"^\+?[0-9 .\-()]{6,30}$")


def texte_obligatoire(valeur: str | None, champ: str, longueur_max: int) -> str:
    """Texte non vide, sans espaces,longueur limitée"""
    valeur = (valeur or "").strip()
    if not valeur:
        raise DonneesInvalides(f"Le champ « {champ} » est obligatoire.")
    if len(valeur) > longueur_max:
        raise DonneesInvalides(
            f"Le champ « {champ} » dépasse {longueur_max} caractères."
        )
    return valeur


def texte_facultatif(valeur: str | None, champ: str, longueur_max: int) -> str | None:
    """une valeur vide devient None"""
    valeur = (valeur or "").strip()
    if not valeur:
        return None
    return texte_obligatoire(valeur, champ, longueur_max)


def email(valeur: str | None) -> str:
    """Adresse email en minuscules."""
    valeur = (valeur or "").strip().lower()
    if len(valeur) > 255 or not FORMAT_EMAIL.match(valeur):
        raise DonneesInvalides(f"Adresse email invalide : « {valeur} ».")
    return valeur


def telephone(valeur: str | None) -> str | None:
    """Numéro facultatif : chiffres, espaces, points, tirets, parenthèses, + initial."""
    valeur = texte_facultatif(valeur, "téléphone", 30)
    if valeur is not None and not FORMAT_TELEPHONE.match(valeur):
        raise DonneesInvalides(f"Numéro de téléphone invalide : « {valeur} ».")
    return valeur
