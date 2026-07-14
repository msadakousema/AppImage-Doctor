"""Suggest a clean app name from an AppImage filename."""

import re
from pathlib import Path


def suggest_name(appimage_path: str) -> str:
    """
    Turn a filename like 'MuseScore-4.4.4.AppImage' into a suggested
    clean name like 'MuseScore-4.4.4' (user can shorten further).
    """
    stem = Path(appimage_path).name

    # Strip the .AppImage extension (case-insensitive)
    stem = re.sub(r"\.appimage$", "", stem, flags=re.IGNORECASE)

    return stem


def slugify(name: str) -> str:
    """
    Turn a human-friendly name like 'MuseScore' into a safe lowercase
    identifier for use in filenames (e.g. .desktop file name, icon name).
    Example: 'MuseScore' -> 'musescore', 'My Cool App!' -> 'my-cool-app'
    """
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "app"


def name_candidates(appimage_path: str, internal_name: str = "") -> list:
    """
    Returns the available name suggestions for this AppImage, in a sensible
    display order, with duplicates removed. There's no reliable way to know
    which candidate (filename-derived vs. the app's own internal Name=) is
    'better' — it depends entirely on the app, so both are surfaced and the
    user picks.
    """
    filename_guess = suggest_name(appimage_path)
    internal_name = (internal_name or "").strip()

    candidates = [c for c in (filename_guess, internal_name) if c]

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)

    return unique or ["App"]
