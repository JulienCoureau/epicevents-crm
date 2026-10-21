"""Point d'entrée (ligne de commande)"""

from contextlib import contextmanager

import click

from crm import services, views
from crm.auth import (
    AuthentificationError,
    authentifier,
    collaborateur_connecte,
    creer_jeton,
    enregistrer_jeton,
    supprimer_jeton,
)
from crm.database import SessionLocal
from crm.permissions import PermissionRefusee


@contextmanager
def session_authentifiee():
    """Ouvre une session et fournit le collaborateur connecté."""
    with SessionLocal() as session:
        try:
            yield session, collaborateur_connecte(session)
        except (AuthentificationError, PermissionRefusee) as erreur:
            raise click.ClickException(str(erreur)) from None


@click.group()
def cli() -> None:
    """Clients, contrats et événements."""


@cli.command()
@click.option("--email", prompt="Email")
def login(email: str) -> None:
    """Se connecter et ouvrir une session."""
    mot_de_passe = click.prompt("Mot de passe", hide_input=True)
    with SessionLocal() as session:
        try:
            collaborateur = authentifier(session, email, mot_de_passe)
        except AuthentificationError as erreur:
            raise click.ClickException(str(erreur)) from None
        enregistrer_jeton(creer_jeton(collaborateur))
        click.echo(f"Connecté : {collaborateur.nom} ({collaborateur.role.nom}).")


@cli.command()
def whoami() -> None:
    """Afficher l'utilisateur connecté."""
    with session_authentifiee() as (session, collaborateur):
        click.echo(f"{collaborateur.nom} ({collaborateur.role.nom})")


@cli.command()
def logout() -> None:
    """Fermer la session."""
    supprimer_jeton()
    click.echo("Déconnecté.")


@cli.group()
def clients() -> None:
    """Gérer les clients."""


@clients.command("list")
def clients_list() -> None:
    """Afficher tous les clients."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_clients(services.lister_clients(session, collaborateur))


@cli.group()
def contrats() -> None:
    """Gérer les contrats."""


@contrats.command("list")
@click.option("--non-signes", is_flag=True, help="Seulement les contrats non signés.")
@click.option("--non-payes", is_flag=True, help="Seulement les contrats non soldés.")
def contrats_list(non_signes: bool, non_payes: bool) -> None:
    """Afficher les contrats."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_contrats(
            services.lister_contrats(session, collaborateur, non_signes, non_payes)
        )


@cli.group()
def evenements() -> None:
    """Gérer les événements."""


@evenements.command("list")
@click.option("--sans-support", is_flag=True, help="Seulement ceux sans support.")
@click.option(
    "--mes-evenements", is_flag=True, help="Seulement ceux qui me sont attribués."
)
def evenements_list(sans_support: bool, mes_evenements: bool) -> None:
    """Afficher les événements."""
    with session_authentifiee() as (session, collaborateur):
        views.afficher_evenements(
            services.lister_evenements(
                session, collaborateur, sans_support, mes_evenements
            )
        )


if __name__ == "__main__":
    cli()
