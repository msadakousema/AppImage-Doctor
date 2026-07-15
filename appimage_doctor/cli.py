"""Command-line interface for AppImage Doctor."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .naming import name_candidates, slugify
from .inspector import inspect
from .icons import find_icon_file, install_icon, refresh_icon_cache
from .desktop_entry import (
    find_existing_desktop_entry,
    validate_desktop_entry,
    write_desktop_entry,
)
from .system import ensure_executable, update_desktop_database, relocate_appimage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="appimage-doctor",
        description="Set up and repair AppImage desktop integration on Linux.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to an .AppImage file to inspect/fix.",
    )
    parser.add_argument(
        "--scan",
        metavar="DIR",
        nargs="?",
        const="__default__",
        help="Scan a directory for AppImages and report their status "
        "(defaults to ~/Applications if no directory given).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (uses the first name candidate).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed paths and commands as they run.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"appimage-doctor {__version__}",
    )
    return parser


def prompt_for_name(candidates: list, assume_yes: bool) -> str:
    """Ask the user to pick a name, or type their own. Returns the chosen name."""
    if assume_yes:
        return candidates[0]

    print("\nWhat should this app be called?")
    for i, candidate in enumerate(candidates, start=1):
        print(f"  {i}) {candidate}")
    print("  Or type a custom name.")

    raw = input("Choice [1]: ").strip()

    if not raw:
        return candidates[0]
    if raw.isdigit() and 1 <= int(raw) <= len(candidates):
        return candidates[int(raw) - 1]
    return raw


def confirm(question: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    raw = input(f"{question} [Y/n]: ").strip().lower()
    return raw in ("", "y", "yes")


def run_setup_flow(appimage_path: str, args: argparse.Namespace) -> int:
    """First-time setup: no existing .desktop entry found for this AppImage."""
    print("This looks like a new AppImage. Let's set it up.\n")

    changed = ensure_executable(
        appimage_path, dry_run=args.dry_run, verbose=args.verbose
    )
    print(
        f"  {'Would set' if args.dry_run else 'Set'} executable permission"
        f"{' (chmod +x)' if changed else ' (already executable)'}"
    )

    print("\nReading AppImage metadata...")
    info = inspect(appimage_path)

    candidates = name_candidates(appimage_path, info.name)
    chosen_name = prompt_for_name(candidates, args.yes)
    slug = slugify(chosen_name)
    print(f'→ Using "{chosen_name}"')

    if not confirm(f'\nSet up desktop integration for "{chosen_name}"?', args.yes):
        print("Cancelled.")
        return 1

    print("\nSetting up desktop integration...")

    new_path = relocate_appimage(
        appimage_path, slug, dry_run=args.dry_run, verbose=args.verbose
    )
    if new_path != Path(appimage_path).resolve():
        print(
            f"  {'Would move' if args.dry_run else 'Moved'} AppImage " f"→ {new_path}"
        )
        appimage_path = str(new_path)

    icon_path = find_icon_file(info.extract_dir, info.icon_name)
    if icon_path:
        installed_icon = install_icon(icon_path, slug, dry_run=args.dry_run)
        print(
            f"  {'Would install' if args.dry_run else 'Installed'} icon "
            f"→ {installed_icon}"
        )
    else:
        print("  ⚠ No icon found inside the AppImage — skipping icon install.")

    desktop_path = write_desktop_entry(
        chosen_name, appimage_path, slug, dry_run=args.dry_run
    )
    print(f"  {'Would create' if args.dry_run else 'Created'} {desktop_path}")

    refresh_icon_cache(dry_run=args.dry_run, verbose=args.verbose)
    update_desktop_database(dry_run=args.dry_run, verbose=args.verbose)
    print("  Refreshed desktop database and icon cache")

    if args.dry_run:
        print("\n(dry run — nothing was actually changed)")
    else:
        print(f"\n{chosen_name} is ready! You should see it in your app grid.")
        print(
            "(Log out/in if it doesn't appear immediately — GNOME Wayland limitation.)"
        )

    return 0


def run_repair_flow(
    appimage_path: str, desktop_path: Path, args: argparse.Namespace
) -> int:
    """Repair: a .desktop entry already references this AppImage — check it's healthy."""
    print(f"Found existing desktop entry: {desktop_path}\n")

    issues = validate_desktop_entry(desktop_path, appimage_path)
    changed_exec = ensure_executable(appimage_path, dry_run=True, verbose=False)

    if not issues and not changed_exec:
        print("  ✓ Executable bit set")
        print("  ✓ .desktop file looks correct")
        print("\nEverything looks fine — no fixes needed.")
        return 0

    if changed_exec:
        print("  ✗ Executable bit:  not set")
    else:
        print("  ✓ Executable bit set")

    for description in issues.values():
        print(f"  ✗ {description}")

    total_issues = len(issues) + (1 if changed_exec else 0)
    if not confirm(f"\n{total_issues} issue(s) found. Apply fixes?", args.yes):
        print("Cancelled.")
        return 1

    ensure_executable(appimage_path, dry_run=args.dry_run, verbose=args.verbose)

    info = inspect(appimage_path)
    slug = desktop_path.stem
    chosen_name = info.name or slug

    icon_path = find_icon_file(info.extract_dir, info.icon_name)
    if icon_path:
        installed_icon = install_icon(icon_path, slug, dry_run=args.dry_run)
        print(
            f"  {'Would install' if args.dry_run else 'Installed'} icon "
            f"→ {installed_icon}"
        )

    write_desktop_entry(chosen_name, appimage_path, slug, dry_run=args.dry_run)
    print(f"  {'Would update' if args.dry_run else 'Updated'} {desktop_path}")

    refresh_icon_cache(dry_run=args.dry_run, verbose=args.verbose)
    update_desktop_database(dry_run=args.dry_run, verbose=args.verbose)
    print("  Refreshed desktop database and icon cache")

    if args.dry_run:
        print("\n(dry run — nothing was actually changed)")
    else:
        print(
            "\nDone. You may need to log out and back in for GNOME Shell "
            "to pick up the changes (Wayland limitation)."
        )

    return 0


def run_scan(directory: str, args: argparse.Namespace) -> int:
    if directory == "__default__":
        directory = str(Path.home() / "Applications")

    scan_dir = Path(directory).expanduser()
    if not scan_dir.exists():
        print(f"Directory not found: {scan_dir}")
        return 1

    appimages = sorted(scan_dir.glob("*.AppImage"))
    if not appimages:
        print(f"No AppImages found in {scan_dir}")
        return 0

    print(f"Scanning {len(appimages)} AppImage(s) in {scan_dir}...\n")

    for appimage in appimages:
        existing = find_existing_desktop_entry(str(appimage))
        if existing is None:
            print(f"  {appimage.name:<45} not set up")
            continue

        issues = validate_desktop_entry(existing, str(appimage))
        if issues:
            print(f"  {appimage.name:<45} {len(issues)} issue(s)")
        else:
            print(f"  {appimage.name:<45} OK")

    print("\nRun `appimage-doctor <file>` on any entry to see details and apply fixes.")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.scan is not None:
        return run_scan(args.scan, args)

    if not args.path:
        parser.print_help()
        return 1

    appimage_path = str(Path(args.path).expanduser().resolve())

    if not Path(appimage_path).exists():
        print(f"File not found: {appimage_path}")
        return 1

    print("AppImage Doctor\n")

    existing_desktop = find_existing_desktop_entry(appimage_path)

    if existing_desktop is None:
        return run_setup_flow(appimage_path, args)
    else:
        return run_repair_flow(appimage_path, existing_desktop, args)


if __name__ == "__main__":
    sys.exit(main())
