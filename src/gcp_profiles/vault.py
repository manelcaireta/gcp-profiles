import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich import print  # noqa: A004

from gcp_profiles.utils import run_command


@dataclass
class Profile:
    name: str


CHECK = "[green bold]✓[reset]"


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
        self._create_or_activate_gcloud_configuration(profile.name)

        print("Step 1/2: Login for the gcloud cli...")
        self._gcloud_login()

        print("\nStep 2/2: Application Default Login (for your code)...")
        self._gcloud_adc_login()

        self._capture_adc(profile.name)

        print("\nYou can now safely switch to other profiles.")

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

    def _create_or_activate_gcloud_configuration(self, name: str) -> None:
        """
        Attempts to create a new configuration or activate an already existing one.
        """

        try:
            self._create_gcloud_configuration(name)
        except subprocess.CalledProcessError:
            print(
                f"[yellow][bold]Warning[/yellow]:[/bold] gcloud configuration '{name}' "
                "already exists, activating...",
            )
            self._switch_gcloud_configuration(name)

    def _create_gcloud_configuration(self, name: str) -> None:
        run_command(
            ["gcloud", "config", "configurations", "create", name],
            reraise=True,
        )
        print(f"{CHECK} Created gcloud configuration '{name}'")

    def _switch_gcloud_configuration(self, name: str) -> None:
        run_command(["gcloud", "config", "configurations", "activate", name])
        print(f"{CHECK} gcloud configuration '{name}' activated")

    def _gcloud_login(self) -> None:
        """Performs the standard Login (for CLI tools)."""
        run_command(["gcloud", "auth", "login"])
        print(f"{CHECK} gcloud auth properly set")

    def _gcloud_adc_login(self) -> None:
        """Performs the ADC Login (for code/libraries)."""
        run_command(["gcloud", "auth", "application-default", "login"])

        if not self.DEFAULT_ADC_PATH.exists():
            msg = "Error: ADC file was not generated. Login may have failed."
            raise RuntimeError(msg)

        print(f"{CHECK} ADC properly set")

    def _capture_adc(self, profile_name: str) -> None:
        profile_dir = self.PROFILES_DIR / profile_name
        shutil.copy(self.DEFAULT_ADC_PATH, profile_dir / self.ADC_FILENAME)
        print(
            f"\n{CHECK} Credentials captured and stored in vault: "
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
            available_profiles = (p.name for p in self.list_profiles())
            msg = (
                f"Profile '{profile.name}' not found in vault.\n"
                f"\nAvailable profiles:\n {', '.join(available_profiles)}"
            )
            raise ValueError(msg)

        credentials = profile_dir / self.ADC_FILENAME

        if not credentials.exists():
            msg = f"No credentials file found for '{profile.name}'."
            raise ValueError(msg)

        self._switch_gcloud_configuration(profile.name)
        self._override_adc(credentials)

    def _override_adc(self, path: Path) -> None:
        try:
            shutil.copy(path, self.DEFAULT_ADC_PATH)
        except Exception as e:
            msg = f"Error copying credentials: {e}"
            raise RuntimeError(msg) from e
        else:
            print(f"{CHECK} application default credentials set to: {path}")

    def delete_profile(self, profile: Profile) -> None:
        profile_dir = self.PROFILES_DIR / profile.name

        if not profile_dir.exists():
            msg = f"Profile '{profile.name}' not found in vault."
            raise ValueError(msg)

        shutil.rmtree(profile_dir)
        print(f"Profile '{profile.name}' deleted from vault.")
