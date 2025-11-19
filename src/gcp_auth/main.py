import typer
from rich import print  # noqa: A004

from gcp_auth.vault import GCPAuthVault, Profile

vault = GCPAuthVault()

app = typer.Typer()


@app.command()
def create(profile_name: str, *, force: bool = False) -> None:
    vault.register(Profile(name=profile_name), force=force)


@app.command()
def list() -> None:  # noqa: A001
    for profile in vault.list_profiles():
        print(profile.name)


@app.command()
def activate(profile_name: str) -> None:
    vault.set_active_profile(Profile(name=profile_name))
