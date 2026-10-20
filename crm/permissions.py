"""Autorisation : qui a le droit de faire quoi."""

from enum import Enum

from crm.models import Client, Collaborateur, Contrat, Evenement


class Action(Enum):
    """Actions soumises à autorisation."""

    LIRE = "lire"
    CREER_COLLABORATEUR = "créer un collaborateur"
    MODIFIER_COLLABORATEUR = "modifier un collaborateur"
    SUPPRIMER_COLLABORATEUR = "supprimer un collaborateur"
    CREER_CLIENT = "créer un client"
    MODIFIER_CLIENT = "modifier un client"
    CREER_CONTRAT = "créer un contrat"
    MODIFIER_CONTRAT = "modifier un contrat"
    CREER_EVENEMENT = "créer un événement"
    MODIFIER_EVENEMENT = "modifier un événement"


class PermissionRefusee(Exception):
    """Levée quand le collaborateur n'a pas le droit d'effectuer l'action."""


# Conditions de propriété


def _toujours(collaborateur: Collaborateur, objet: object) -> bool:
    """Aucune condition : le rôle suffit."""
    return True


def _est_son_client(collaborateur: Collaborateur, client: Client) -> bool:
    """Le client est suivi par ce commercial."""
    return client is not None and client.commercial_id == collaborateur.id


def _est_contrat_de_son_client(collaborateur: Collaborateur, contrat: Contrat) -> bool:
    """Le contrat concerne un client suivi par ce commercial."""
    return contrat is not None and _est_son_client(collaborateur, contrat.client)


def _est_son_evenement(collaborateur: Collaborateur, evenement: Evenement) -> bool:
    """L'événement est attribué à ce collaborateur support."""
    return evenement is not None and evenement.support_id == collaborateur.id


# La matrice : rôle - action - condition

PERMISSIONS = {
    "gestion": {
        Action.LIRE: _toujours,
        Action.CREER_COLLABORATEUR: _toujours,
        Action.MODIFIER_COLLABORATEUR: _toujours,
        Action.SUPPRIMER_COLLABORATEUR: _toujours,
        Action.CREER_CONTRAT: _toujours,
        Action.MODIFIER_CONTRAT: _toujours,
        Action.MODIFIER_EVENEMENT: _toujours,
    },
    "commercial": {
        Action.LIRE: _toujours,
        Action.CREER_CLIENT: _toujours,
        Action.MODIFIER_CLIENT: _est_son_client,
        Action.MODIFIER_CONTRAT: _est_contrat_de_son_client,
        Action.CREER_EVENEMENT: _est_contrat_de_son_client,
    },
    "support": {
        Action.LIRE: _toujours,
        Action.MODIFIER_EVENEMENT: _est_son_evenement,
    },
}


def a_le_droit(collaborateur: Collaborateur, action: Action, objet=None) -> bool:
    """Retourne True si le collaborateur peut effectuer l'action sur l'objet."""
    regles = PERMISSIONS.get(collaborateur.role.nom, {})
    condition = regles.get(action)
    if condition is None:
        return False
    return condition(collaborateur, objet)


def verifier(collaborateur: Collaborateur, action: Action, objet=None) -> None:
    """Lève PermissionRefusee si le collaborateur n'a pas le droit."""
    if not a_le_droit(collaborateur, action, objet):
        raise PermissionRefusee(f"Vous n'avez pas le droit de {action.value}.")
