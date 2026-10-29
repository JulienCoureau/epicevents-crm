"""Affichage en tableaux"""

from rich.console import Console
from rich.table import Table

from crm.models import Client, Contrat, Evenement

console = Console()

FORMAT_DATE = "%d/%m/%Y"
FORMAT_DATE_HEURE = "%d/%m/%Y %H:%M"


def _afficher(table: Table, nb_lignes: int, message_si_vide: str) -> None:
    """Affiche le tableau, ou un message s'il n'y a rien à montrer."""
    if nb_lignes == 0:
        console.print(f"[italic]{message_si_vide}[/italic]")
    else:
        console.print(table)


def afficher_clients(clients: list[Client]) -> None:
    """Tableau des clients."""
    table = Table(title="Clients")
    for colonne in (
        "ID",
        "Nom",
        "Email",
        "Téléphone",
        "Entreprise",
        "Commercial",
        "Créé le",
        "Mis à jour le",
    ):
        table.add_column(colonne, overflow="fold")
    for client in clients:
        table.add_row(
            str(client.id),
            client.nom_complet,
            client.email,
            client.telephone or "",
            client.entreprise or "",
            client.commercial.nom,
            client.date_creation.strftime(FORMAT_DATE),
            client.derniere_mise_a_jour.strftime(FORMAT_DATE),
        )
    _afficher(table, len(clients), "Aucun client.")


def afficher_contrats(contrats: list[Contrat]) -> None:
    """Tableau des contrats."""
    table = Table(title="Contrats")
    for colonne in (
        "ID",
        "Client",
        "Commercial",
        "Montant total",
        "Reste à payer",
        "Créé le",
        "Signé",
    ):
        table.add_column(colonne, overflow="fold")
    for contrat in contrats:
        table.add_row(
            str(contrat.id),
            contrat.client.nom_complet,
            contrat.client.commercial.nom,
            f"{contrat.montant_total:.2f} €",
            f"{contrat.montant_restant:.2f} €",
            contrat.date_creation.strftime(FORMAT_DATE),
            "Oui" if contrat.signe else "Non",
        )
    _afficher(table, len(contrats), "Aucun contrat.")


def afficher_evenements(evenements: list[Evenement]) -> None:
    """Tableau des événements."""
    table = Table(title="Événements")
    for colonne in (
        "ID",
        "Nom",
        "Contrat",
        "Client",
        "Contact client",
        "Début",
        "Fin",
        "Support",
        "Lieu",
        "Participants",
    ):
        table.add_column(colonne, overflow="fold")
    for evenement in evenements:
        client = evenement.contrat.client
        table.add_row(
            str(evenement.id),
            evenement.nom,
            str(evenement.contrat_id),
            client.nom_complet,
            f"{client.email}\n{client.telephone or ''}",
            evenement.date_debut.strftime(FORMAT_DATE_HEURE),
            evenement.date_fin.strftime(FORMAT_DATE_HEURE),
            evenement.support.nom if evenement.support else "[red]À attribuer[/red]",
            evenement.lieu,
            str(evenement.participants),
        )
    _afficher(table, len(evenements), "Aucun événement.")
