import subprocess
import sys


def run_command(
    command: list[str],
    *,
    shell: bool = False,
    reraise: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """Runs a shell command and checks for errors."""
    try:
        return subprocess.run(  # noqa: S603
            command,
            check=True,
            shell=shell,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        if reraise:
            raise

        print(f"\nError executing command: {' '.join(command)}")
        print(e)
        sys.exit(1)
