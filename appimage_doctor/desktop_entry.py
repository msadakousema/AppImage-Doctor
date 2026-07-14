"""Write and validate ~/.local/share/applications/*.desktop entries for AppImages."""

from pathlib import Path
from typing import Optional

APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"


def build_desktop_entry(name: str, appimage_path: str, slug: str) -> str:
    """
    Build the contents of a .desktop file that correctly points at the
    real, current location of the AppImage on disk.
    """
    appimage_path = str(Path(appimage_path).resolve())

    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        f'Exec="{appimage_path}" %U\n'
        f"Icon={slug}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        f"X-AppImage-Doctor-Managed=true\n"
    )


def write_desktop_entry(
    name: str, appimage_path: str, slug: str, dry_run: bool = False
) -> Path:
    """
    Write the .desktop file to ~/.local/share/applications/<slug>.desktop.
    Returns the path it was (or would be) written to.
    """
    dest_path = APPLICATIONS_DIR / f"{slug}.desktop"
    content = build_desktop_entry(name, appimage_path, slug)

    if not dry_run:
        APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")
        dest_path.chmod(0o755)

    return dest_path


def find_existing_desktop_entry(appimage_path: str) -> Optional[Path]:
    """
    Search installed .desktop files for one whose Exec= line already
    references this exact AppImage path. Used to decide whether this is
    a first-time setup or a repair of something already integrated.
    """
    appimage_path = str(Path(appimage_path).resolve())

    if not APPLICATIONS_DIR.exists():
        return None

    for desktop_file in APPLICATIONS_DIR.glob("*.desktop"):
        try:
            text = desktop_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in text.splitlines():
            if line.strip().startswith("Exec=") and appimage_path in line:
                return desktop_file

    return None


def validate_desktop_entry(desktop_path: Path, appimage_path: str) -> dict:
    """
    Check an existing .desktop file for the classic breakages:
    - Exec= pointing at a path that no longer exists (moved/deleted AppImage)
    - Exec= not matching the AppImage path we're currently inspecting
    Returns a dict of issue -> description, empty if everything looks fine.
    """
    issues = {}
    appimage_path = str(Path(appimage_path).resolve())

    if not desktop_path.exists():
        issues["missing_desktop_file"] = "No .desktop file found."
        return issues

    text = desktop_path.read_text(encoding="utf-8", errors="replace")
    exec_line = ""
    icon_line = ""

    for line in text.splitlines():
        if line.strip().startswith("Exec="):
            exec_line = line.strip()[len("Exec=") :]
        elif line.strip().startswith("Icon="):
            icon_line = line.strip()[len("Icon=") :]

    if appimage_path not in exec_line:
        issues["stale_exec_path"] = (
            f"Exec= does not point to the current AppImage location "
            f"({appimage_path})."
        )

    if not icon_line:
        issues["missing_icon_field"] = "No Icon= field set in the .desktop file."

    return issues
