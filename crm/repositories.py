"""Accès aux données"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from crm.models import Client, Contrat, Evenement


class Repository:
    """Base commune : garde la session et retrouve un objet par son id."""

    modele = None

    def __init__(self, session: Session) -> None:
        self.session = session

    def obtenir(self, identifiant: int):
        """Retourne l'objet d'id donné, ou None s'il n'existe pas."""
        return self.session.get(self.modele, identifiant)


class ClientRepository(Repository):
    """Requêtes sur les clients."""

    modele = Client

    def lister(self) -> list[Client]:
        """Tous les clients, par ordre d'id."""
        return list(self.session.scalars(select(Client).order_by(Client.id)))


class ContratRepository(Repository):
    """Requêtes sur les contrats."""

    modele = Contrat

    def lister(
        self, non_signes: bool = False, non_payes: bool = False
    ) -> list[Contrat]:
        """Les contrats, éventuellement filtrés."""
        requete = select(Contrat).order_by(Contrat.id)
        if non_signes:
            requete = requete.where(Contrat.signe.is_(False))
        if non_payes:
            requete = requete.where(Contrat.montant_restant > 0)
        return list(self.session.scalars(requete))


class EvenementRepository(Repository):
    """Requêtes sur les événements."""

    modele = Evenement

    def lister(
        self, sans_support: bool = False, support_id: int | None = None
    ) -> list[Evenement]:
        """Les événements par date de début, éventuellement filtrés."""
        requete = select(Evenement).order_by(Evenement.date_debut)
        if sans_support:
            requete = requete.where(Evenement.support_id.is_(None))
        if support_id is not None:
            requete = requete.where(Evenement.support_id == support_id)
        return list(self.session.scalars(requete))
