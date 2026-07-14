"""Extract an AppImage and read its embedded .desktop metadata."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class AppImageInfo:
    """Holds what we learn from inspecting an AppImage's internals."""

    def __init__(self, name: str, exec_line: str, icon_name: str, extract_dir: Path):
        self.name = name
        self.exec_line = exec_line
        self.icon_name = icon_name
        self.extract_dir = extract_dir

    def __repr__(self) -> str:
        return (
            f"AppImageInfo(name={self.name!r}, exec={self.exec_line!r}, "
            f"icon={self.icon_name!r})"
        )


def extract_appimage(appimage_path: str) -> Path:
    """
    Runs the AppImage's built-in --appimage-extract into a temp directory
    and returns the path to the resulting squashfs-root folder.
    """
    appimage_path = str(Path(appimage_path).resolve())
    work_dir = Path(tempfile.mkdtemp(prefix="appimage-doctor-"))

    result = subprocess.run(
        [appimage_path, "--appimage-extract"],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to extract AppImage:\n{result.stderr.strip()}")

    squashfs_root = work_dir / "squashfs-root"
    if not squashfs_root.exists():
        raise RuntimeError(
            f"Extraction succeeded but squashfs-root not found in {work_dir}"
        )

    return squashfs_root


def parse_desktop_file(desktop_path: Path) -> dict:
    """
    Very small .desktop file parser — just enough to pull out
    Name=, Exec=, Icon= from the [Desktop Entry] section.
    """
    values = {}
    in_desktop_entry = False

    with open(desktop_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                in_desktop_entry = line == "[Desktop Entry]"
                continue
            if not in_desktop_entry or not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()

    return values


def find_internal_desktop_file(squashfs_root: Path) -> Optional[Path]:
    """Finds the .desktop file bundled inside the extracted AppImage."""
    matches = list(squashfs_root.glob("*.desktop"))
    return matches[0] if matches else None


def inspect(appimage_path: str) -> AppImageInfo:
    """
    Full inspection pipeline: extract, find the internal .desktop file,
    and pull out Name/Exec/Icon.
    """
    squashfs_root = extract_appimage(appimage_path)
    desktop_file = find_internal_desktop_file(squashfs_root)

    if desktop_file is None:
        raise RuntimeError(
            "No .desktop file found inside the AppImage — cannot read metadata."
        )

    values = parse_desktop_file(desktop_file)

    return AppImageInfo(
        name=values.get("Name", ""),
        exec_line=values.get("Exec", ""),
        icon_name=values.get("Icon", ""),
        extract_dir=squashfs_root,
    )
