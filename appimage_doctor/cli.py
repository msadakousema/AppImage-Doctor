"""Command-line interface for AppImage Doctor."""

import argparse
import sys

from . import __version__


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
        help="Skip confirmation prompts.",
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.scan is not None:
        print(f"[stub] would scan: {args.scan}")
        return 0

    if not args.path:
        parser.print_help()
        return 1

    print(f"[stub] would inspect: {args.path} (dry_run={args.dry_run})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
