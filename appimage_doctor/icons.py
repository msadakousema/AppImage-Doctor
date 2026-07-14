"""Find and install AppImage icons following the freedesktop hicolor icon theme spec."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
except ImportError:
    Image = None

STANDARD_SIZES = [16, 22, 24, 32, 48, 64, 96, 128, 192, 256, 512]

ICONS_BASE = Path.home() / ".local" / "share" / "icons" / "hicolor"


def find_icon_file(squashfs_root: Path, icon_name: str) -> Optional[Path]:
    """
    Look for the icon referenced by Icon= inside the extracted AppImage.
    Tries exact name matches first (.png, .svg), then falls back to
    the .DirIcon that most AppImages include at their root.
    """
    if icon_name:
        for ext in (".png", ".svg"):
            candidate = squashfs_root / f"{icon_name}{ext}"
            if candidate.exists():
                return candidate

        # Sometimes the icon lives in a subfolder (e.g. usr/share/icons/...)
        matches = list(squashfs_root.rglob(f"{icon_name}.png")) + list(
            squashfs_root.rglob(f"{icon_name}.svg")
        )
        if matches:
            return matches[0]

    dir_icon = squashfs_root / ".DirIcon"
    if dir_icon.exists():
        return dir_icon

    return None


def _nearest_standard_size(pixel_size: int) -> int:
    """Pick the closest standard hicolor size folder for a given pixel dimension."""
    return min(STANDARD_SIZES, key=lambda s: abs(s - pixel_size))


def install_icon(icon_path: Path, slug: str, dry_run: bool = False) -> Path:
    """
    Install the given icon file into ~/.local/share/icons/hicolor/<size>/apps/
    (or scalable/apps/ for SVGs), named after the app's slug.

    Returns the path the icon was (or would be) installed to.
    """
    suffix = icon_path.suffix.lower()

    if suffix == ".svg":
        dest_dir = ICONS_BASE / "scalable" / "apps"
        dest_path = dest_dir / f"{slug}.svg"
    else:
        # Default to .png handling — also covers the .DirIcon fallback case,
        # which is usually a PNG even without the extension.
        size = 256
        if Image is not None:
            try:
                with Image.open(icon_path) as img:
                    width, _ = img.size
                    size = _nearest_standard_size(width)
            except Exception:
                pass  # fall back to default size if Pillow can't read it

        dest_dir = ICONS_BASE / f"{size}x{size}" / "apps"
        dest_path = dest_dir / f"{slug}.png"

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(icon_path, dest_path)

    return dest_path


def refresh_icon_cache(dry_run: bool = False, verbose: bool = False) -> None:
    """Force GTK to rebuild the icon cache so the new icon shows up immediately."""
    cmd = ["gtk-update-icon-cache", "-f", str(ICONS_BASE)]

    if verbose:
        print(f"$ {' '.join(cmd)}")

    if dry_run:
        return

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        if verbose:
            print("  (gtk-update-icon-cache not found, skipping)")
