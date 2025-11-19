import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from rich import print  # noqa: A004

from gcp_profiles.vault import GCPAuthVault, Profile

vault = GCPAuthVault()

app = typer.Typer()


@contextmanager
def handle_errors() -> Iterator:
    try:
        vault.check_gcloud_installed()
        yield
    except Exception as e:
        stem = Path(sys.argv[0]).stem
        print(f"[red bold]{stem}[/red bold]: {e}")
        raise typer.Exit(code=1) from e


ProfileArgument = Annotated[str, typer.Argument(help="Name of the profile.")]
ForceOption = Annotated[bool, typer.Option(help="Overwrite existing profile.")]


@app.command()
def create(profile: ProfileArgument, *, force: ForceOption = False) -> None:
    """
    Creates a new profile in the vault.

    Arguments:
        force(bool): Whether to overwrite an existing profile with the same name.
    """

    with handle_errors():
        vault.register(Profile(name=profile), force=force)


@app.command()
def list() -> None:  # noqa: A001
    """
    Lists all profiles in the vault.
    """

    with handle_errors():
        for profile in vault.list_profiles():
            print(profile.name)


@app.command()
def activate(profile: ProfileArgument) -> None:
    """
    Activates a profile.
    """

    with handle_errors():
        vault.set_active_profile(Profile(name=profile))


@app.command()
def delete(profile: ProfileArgument) -> None:
    """
    Deletes a profile from the vault.
    """

    with handle_errors():
        vault.delete_profile(Profile(name=profile))
