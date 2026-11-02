"""Erreurs métier, toute autre exception est inattendue : c'est un bug, qui sera signalé à Sentry"""


class ErreurMetier(Exception):
    """Classe mère de toutes les erreurs prévues de l'application"""


class DonneesInvalides(ErreurMetier):
    """Une donnée saisie ne respecte pas les règles (format, longueur, unicité)"""


class ObjetIntrouvable(ErreurMetier):
    """L'objet demandé n'existe pas en base"""