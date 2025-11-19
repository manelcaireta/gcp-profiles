import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from rich import print  # noqa: A004

from gcp_auth.vault import GCPAuthVault, Profile

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


@app.command()
def create(profile_name: str, *, force: bool = False) -> None:
    with handle_errors():
        vault.register(Profile(name=profile_name), force=force)


@app.command()
def list() -> None:  # noqa: A001
    with handle_errors():
        for profile in vault.list_profiles():
            print(profile.name)


@app.command()
def activate(profile_name: str) -> None:
    with handle_errors():
        vault.set_active_profile(Profile(name=profile_name))


@app.command()
def delete(profile_name: str) -> None:
    with handle_errors():
        vault.delete_profile(Profile(name=profile_name))
