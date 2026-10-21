"""Vérifie les droits"""

from sqlalchemy.orm import Session

from crm.models import Client, Collaborateur, Contrat, Evenement
from crm.permissions import Action, verifier
from crm.repositories import ClientRepository, ContratRepository, EvenementRepository


def lister_clients(session: Session, collaborateur: Collaborateur) -> list[Client]:
    """Tous les clients, pour un collaborateur autorisé à lire."""
    verifier(collaborateur, Action.LIRE)
    return ClientRepository(session).lister()


def lister_contrats(
    session: Session,
    collaborateur: Collaborateur,
    non_signes: bool = False,
    non_payes: bool = False,
) -> list[Contrat]:
    """Les contrats, éventuellement filtrés."""
    verifier(collaborateur, Action.LIRE)
    return ContratRepository(session).lister(non_signes, non_payes)


def lister_evenements(
    session: Session,
    collaborateur: Collaborateur,
    sans_support: bool = False,
    mes_evenements: bool = False,
) -> list[Evenement]:
    """Les événements, éventuellement filtrés ; « mes événements » pour le support."""
    verifier(collaborateur, Action.LIRE)
    support_id = collaborateur.id if mes_evenements else None
    return EvenementRepository(session).lister(sans_support, support_id)
