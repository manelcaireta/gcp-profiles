import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Profile:
    name: str


class GCPAuthVault:
    def __init__(self) -> None:
        self.VAULT_DIR = Path.home() / ".gcp-auth"

        if os.name == "nt":
            self.GCLOUD_CONFIG_DIR = Path(os.environ.get("APPDATA")) / "gcloud"
        else:
            self.GCLOUD_CONFIG_DIR = Path.home() / ".config" / "gcloud"

        self.ensure_vault()

    def ensure_vault(self) -> None:
        """Creates the storage directory if it doesn't exist."""
        if not self.VAULT_DIR.exists():
            self.VAULT_DIR.mkdir(parents=True)

    def is_gcloud_installed(self) -> bool:
        return shutil.which("gcloud") is not None
