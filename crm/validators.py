"""Validation des données saisies : nettoyage et vérification avant écriture"""

import re

from crm.exceptions import DonneesInvalides
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from datetime import datetime

FORMAT_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FORMAT_TELEPHONE = re.compile(r"^\+?[0-9 .\-()]{6,30}$")
MONTANT_MAX = Decimal("99999999.99")
FORMAT_DATE_HEURE = "%d/%m/%Y %H:%M"
FUSEAU = ZoneInfo("Europe/Paris")
PARTICIPANTS_MAX = 100_000  # par feu faute de frappes


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


def montant(valeur, champ: str) -> Decimal:
    """Montant positif ou nul."""
    texte = str(valeur).strip().replace(" ", "").replace(",", ".")
    try:
        nombre = Decimal(texte)
    except InvalidOperation:
        raise DonneesInvalides(f"« {champ} » doit être un nombre.") from None
    if not nombre.is_finite():
        raise DonneesInvalides(f"« {champ} » doit être un nombre.")
    if nombre < 0:
        raise DonneesInvalides(f"« {champ} » ne peut pas être négatif.")
    if nombre > MONTANT_MAX:
        raise DonneesInvalides(f"« {champ} » est trop grand.")
    if nombre != nombre.quantize(Decimal("0.01")):
        raise DonneesInvalides(f"« {champ} » : deux décimales maximum.")
    return nombre.quantize(Decimal("0.01"))


def date_heure(valeur: str | None, champ: str) -> datetime:
    """Date et heure au format JJ/MM/AAAA HH:MM, à l'heure de Paris."""
    texte = (valeur or "").strip()
    try:
        moment = datetime.strptime(texte, FORMAT_DATE_HEURE)
    except ValueError:
        raise DonneesInvalides(
            f"« {champ} » : format attendu JJ/MM/AAAA HH:MM."
        ) from None
    return moment.replace(tzinfo=FUSEAU)


def nombre_participants(valeur) -> int:
    """Nombre entier, positif ou nul, de participants."""
    try:
        nombre = int(str(valeur).strip())
    except ValueError:
        raise DonneesInvalides(
            "Le nombre de participants doit être un entier."
        ) from None
    if nombre < 0:
        raise DonneesInvalides("Le nombre de participants ne peut pas être négatif.")
    if nombre > PARTICIPANTS_MAX:
        raise DonneesInvalides("Le nombre de participants est trop grand.")
    return nombre
