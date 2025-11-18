import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from gcp_auth.utils import run_command


@dataclass
class Profile:
    name: str


class GCPAuthVault:
    def __init__(self) -> None:
        self.VAULT_DIR = Path.home() / ".gcp-auth"
        self.PROFILES_DIR = self.VAULT_DIR / "profiles"

        if os.name == "nt":
            self.GCLOUD_CONFIG_DIR = Path(os.environ.get("APPDATA")) / "gcloud"
        else:
            self.GCLOUD_CONFIG_DIR = Path.home() / ".config" / "gcloud"

        self.ADC_FILENAME = "application_default_credentials.json"
        self.DEFAULT_ADC_PATH = self.GCLOUD_CONFIG_DIR / self.ADC_FILENAME

        self.ensure_vault()

    def ensure_vault(self) -> None:
        """Creates the storage directory if it doesn't exist."""
        if not self.PROFILES_DIR.exists():
            self.PROFILES_DIR.mkdir(parents=True)

    def is_gcloud_installed(self) -> bool:
        return shutil.which("gcloud") is not None

    def register(self, profile: Profile, *, force: bool = False) -> None:
        profile_dir = self.PROFILES_DIR / profile.name

        if profile_dir.exists() and not force:
            msg = (
                f"Profile '{profile.name}' already exists in the manager."
                "Use --force to overwrite."
            )
            raise ValueError(msg)

        self._create_gcloud_configuration(profile.name)
        self._gcloud_login()
        self._gcloud_adc_login()
        self._capture_adc(profile_dir)

        print("You can now safely switch to other profiles.")

    def _create_gcloud_configuration(self, name: str) -> None:
        """
        Attempts to create a new configuration or activate an already existing one.
        """

        try:
            run_command(
                ["gcloud", "config", "configurations", "create", name],
                reraise=True,
            )
            print(f"✓ Created gcloud configuration '{name}'")
        except subprocess.CalledProcessError:
            print(f"gcloud configuration '{name}' already exists, activating...")
            run_command(["gcloud", "config", "configurations", "activate", name])
            print(f"✓ gcloud configuration '{name}' activated")

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

        print("✓ ADC properly set")

    def _capture_adc(self, profile_dir: Path) -> None:
        shutil.copy(self.DEFAULT_ADC_PATH, profile_dir / self.ADC_FILENAME)
        print(f"\n✓ Credentials captured and stored in vault: {profile_dir.resolve()}")

    def list_profiles(self) -> list[Profile]:
        """Lists all stored profiles."""
        if not self.PROFILES_DIR.exists():
            return []

        return [Profile(p.name) for p in self.VAULT_DIR.iterdir() if p.is_dir()]

