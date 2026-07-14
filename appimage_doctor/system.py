"""Small system-level helpers: making files executable, refreshing desktop database."""

import stat
import subprocess
from pathlib import Path


def ensure_executable(path: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Make sure the given file has the executable bit set.
    Returns True if a change was (or would be) made, False if it was
    already executable.
    """
    p = Path(path)
    current_mode = p.stat().st_mode
    is_executable = bool(current_mode & stat.S_IXUSR)

    if is_executable:
        return False

    if verbose:
        print(f"$ chmod +x {p}")

    if not dry_run:
        p.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return True


def update_desktop_database(dry_run: bool = False, verbose: bool = False) -> None:
    """Refresh the desktop file database so app launchers notice the new entry."""
    applications_dir = Path.home() / ".local" / "share" / "applications"
    cmd = ["update-desktop-database", str(applications_dir)]

    if verbose:
        print(f"$ {' '.join(cmd)}")

    if dry_run:
        return

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        if verbose:
            print("  (update-desktop-database not found, skipping)")
