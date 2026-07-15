"""Small system-level helpers: making files executable, refreshing desktop database."""

import shutil
import stat
import subprocess
from pathlib import Path

APPLICATIONS_HOME_DIR = Path.home() / "Applications"


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


def relocate_appimage(
    current_path: str, slug: str, dry_run: bool = False, verbose: bool = False
) -> Path:
    """
    Move the AppImage into ~/Applications/, renamed to match the .desktop
    slug (e.g. 'arduino-ide.AppImage'), creating the folder if needed.
    If it's already there under the right name, this is a no-op.

    Returns the final path the AppImage lives (or would live) at.
    """
    current = Path(current_path).resolve()
    target_dir = APPLICATIONS_HOME_DIR
    target_path = target_dir / f"{slug}.AppImage"

    if current == target_path:
        return current

    if verbose:
        print(f"$ mkdir -p {target_dir}")
        print(f"$ mv {current} {target_path}")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(target_path))

    return target_path
