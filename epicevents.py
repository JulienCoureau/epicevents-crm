"""Point d'entrée"""

import click

from crm.auth import (
    AuthentificationError,
    authentifier,
    collaborateur_connecte,
    creer_jeton,
    enregistrer_jeton,
    supprimer_jeton,
)
from crm.database import SessionLocal


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
    with SessionLocal() as session:
        try:
            collaborateur = collaborateur_connecte(session)
        except AuthentificationError as erreur:
            raise click.ClickException(str(erreur)) from None
        click.echo(f"{collaborateur.nom} ({collaborateur.role.nom})")


@cli.command()
def logout() -> None:
    """Fermer la session."""
    supprimer_jeton()
    click.echo("Déconnecté.")


if __name__ == "__main__":
    cli()
