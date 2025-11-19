import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from rich import print  # noqa: A004

from gcp_auth.utils import run_command


@dataclass
class Profile:
    name: str


class GCPAuthVault:
    def __init__(self) -> None:
        self.VAULT_DIR = Path.home() / ".config" / "gcp-auth"
        self.PROFILES_DIR = self.VAULT_DIR / "profiles"
        self.GCLOUD_CONFIG_DIR = Path.home() / ".config" / "gcloud"
        self.ADC_FILENAME = "application_default_credentials.json"
        self.DEFAULT_ADC_PATH = self.GCLOUD_CONFIG_DIR / self.ADC_FILENAME

        self.ensure_vault()

    def ensure_vault(self) -> None:
        """Creates the storage directory if it doesn't exist."""
        if not self.PROFILES_DIR.exists():
            self.PROFILES_DIR.mkdir(parents=True)

    def check_gcloud_installed(self) -> None:
        if not shutil.which("gcloud"):
            msg = "gcloud is not installed or not in PATH"
            raise RuntimeError(msg)

    def register(self, profile: Profile, *, force: bool = False) -> None:
        self._create_clean_profile(profile.name, force=force)
        created_new_config = self._create_gcloud_configuration(profile.name)
        if created_new_config:
            self._gcloud_login()
        else:
            print("Step 1/2: Skipping Login (configuration already exists)...")
        self._gcloud_adc_login()
        self._capture_adc(profile.name)

        print("You can now safely switch to other profiles.")

    def _create_clean_profile(self, name: str, *, force: bool = False) -> None:
        """Creates a clean profile directory."""
        profile_dir = self.PROFILES_DIR / name

        if profile_dir.exists() and not force:
            msg = (
                f"Profile '{name}' already exists in the manager. "
                "Use --force to overwrite."
            )
            raise ValueError(msg)
        if profile_dir.exists() and force:
            print(f"Overwriting profile '{name}'...")
            shutil.rmtree(profile_dir)
        profile_dir.mkdir(exist_ok=True)

    def _create_gcloud_configuration(self, name: str) -> bool:
        """
        Attempts to create a new configuration or activate an already existing one.

        Returns:
            Weather a new configuration was created
        """

        try:
            run_command(
                ["gcloud", "config", "configurations", "create", name],
                reraise=True,
            )
        except subprocess.CalledProcessError:
            print(
                f"[yellow][bold]Warning[/yellow]:[/bold] gcloud configuration '{name}' "
                "already exists, activating...",
            )
            run_command(["gcloud", "config", "configurations", "activate", name])
            print(f"[green]✓[reset] gcloud configuration '{name}' activated")
            return False
        else:
            print(f"[green]✓[reset] Created gcloud configuration '{name}'")
            return True

    def _gcloud_login(self) -> None:
        """Performs the standard Login (for CLI tools)."""

        print("\nStep 1/2: Standard Login (for CLI tools)...")
        run_command(["gcloud", "auth", "login"])
        print("✓ gcloud auth properly set")

    def _gcloud_adc_login(self) -> None:
        """Performs the ADC Login (for code/libraries)."""

        print("\nStep 2/2: Application Default Login (for your code)...")
        run_command(["gcloud", "auth", "application-default", "login"])

        if not self.DEFAULT_ADC_PATH.exists():
            print("Error: ADC file was not generated. Login may have failed.")
            sys.exit(1)

        print("[green]✓[reset] ADC properly set")

    def _capture_adc(self, profile_name: str) -> None:
        profile_dir = self.PROFILES_DIR / profile_name
        shutil.copy(self.DEFAULT_ADC_PATH, profile_dir / self.ADC_FILENAME)
        print(
            "\n[green]✓[reset] Credentials captured and stored in vault: "
            f"{profile_dir.resolve()}",
        )

    def list_profiles(self) -> list[Profile]:
        """Lists all stored profiles."""
        if not self.PROFILES_DIR.exists():
            return []

        return [Profile(p.name) for p in self.PROFILES_DIR.iterdir() if p.is_dir()]

    def set_active_profile(self, profile: Profile) -> None:
        profile_dir = self.PROFILES_DIR / profile.name

        if not profile_dir.exists():
            print(f"Profile '{profile.name}' not found in vault.")
            print(
                "Available profiles:\n",
                ", ".join(p.name for p in self.list_profiles()),
            )
            sys.exit(1)

        credentials = profile_dir / self.ADC_FILENAME

        if not credentials.exists():
            print(
                f"No credentials file found for '{profile.name}'.",
            )
            sys.exit(1)

        self._switch_gcloud_configuration(profile.name)
        print(f"[green]✓[reset] Set gcloud config to '{profile.name}'")

        self._override_adc(credentials)
        print(f"[green]✓[reset] Restored ADC credentials for '{profile.name}'")

    def _switch_gcloud_configuration(self, profile_name: str) -> None:
        run_command(["gcloud", "config", "configurations", "activate", profile_name])

    def _override_adc(self, path: Path) -> None:
        try:
            shutil.copy(path, self.DEFAULT_ADC_PATH)
        except Exception as e:  # noqa: BLE001
            print(f"Error copying credentials: {e}")
            sys.exit(1)

    def delete_profile(self, profile: Profile) -> None:
        profile_dir = self.PROFILES_DIR / profile.name

        if not profile_dir.exists():
            print(f"Profile '{profile.name}' not found in vault.")
            print(
                "Available profiles:\n",
                ", ".join(p.name for p in self.list_profiles()),
            )
            sys.exit(1)

        shutil.rmtree(profile_dir)
        print(f"Profile '{profile.name}' deleted from vault.")
