# AppImage Doctor

A CLI tool that makes AppImages _just work_ on Linux — no more broken icons,
missing app-grid entries, or launchers that stop working after you move a file.

Built after repeatedly hitting broken AppImage desktop integration on Fedora
(GNOME/Wayland), most recently with MuseScore.

## The problem

AppImages are meant to be portable, single-file apps — but on GNOME/Wayland
they don't integrate with the desktop automatically. Common symptoms:

- The app doesn't show up in your app grid at all
- It shows up with a generic/blank icon instead of its real one
- It launches fine the first time, but breaks after you move or rename the file
- Icon and desktop caches go stale and never refresh on their own

AppImage Doctor diagnoses and fixes all of these, whether you're setting up an
AppImage for the first time or repairing one that's already half-broken.

## What it does

**First-time setup** (new AppImage, no desktop integration yet):

1. Sets the executable bit if it isn't already set
2. Lets you choose a name — suggests both the filename-derived name and the
   app's own internal name, or you can type your own
3. Moves the AppImage into `~/Applications/` (created if missing), renamed to
   match
4. Extracts the icon from inside the AppImage and installs it into the
   correct `~/.local/share/icons/hicolor/<size>/apps/` location per the
   freedesktop icon theme spec
5. Writes a correct `.desktop` file to `~/.local/share/applications/`,
   pointing at the AppImage's real, final path
6. Refreshes the icon cache and desktop database so the app shows up
   immediately

**Repair** (an AppImage that already has a `.desktop` entry):

1. Validates the existing `.desktop` file — checks for a stale `Exec=` path,
   a missing executable bit, or a missing `Icon=` field
2. Reports what's wrong
3. Re-installs the icon and rewrites the `.desktop` file to fix it

**Scan mode**: point it at a directory (defaults to `~/Applications`) and get
a status report across every AppImage found — which ones are fine, which
need setup, which have issues.

## Installation

```bash
git clone <your-repo-url>
cd appimage-doctor
pip install -e . --break-system-packages
```

Requires Python 3.8+ and [Pillow](https://pypi.org/project/Pillow/) (installed
automatically).

## Usage

Set up or repair a single AppImage:

```bash
appimage-doctor ~/Downloads/SomeApp.AppImage
```

Preview changes without touching anything:

```bash
appimage-doctor ~/Downloads/SomeApp.AppImage --dry-run
```

Scan a directory for AppImages and see their status:

```bash
appimage-doctor --scan
appimage-doctor --scan ~/Downloads
```

Skip confirmation prompts (useful for scripting):

```bash
appimage-doctor ~/Downloads/SomeApp.AppImage -y
```

Show detailed commands as they run:

```bash
appimage-doctor ~/Downloads/SomeApp.AppImage -v
```
