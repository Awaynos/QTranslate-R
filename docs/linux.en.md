# QTranslate Remake on Linux

The application runs from source and supports X11 and Wayland. Some features depend on the desktop environment and installed tools.

## Prebuilt packages

Release `v1.1.0` contains:

- `QTranslateRemake-1.1.0-linux-universal-x86_64.AppImage` — universal build, glibc 2.35+;
- `QTranslateRemake-1.1.0-linux-universal.tar.gz` — the same build as an archive;
- `qtranslate-remake-1.1.0-1-x86_64.pkg.tar.zst` — Arch package, dependencies are installed by pacman;
- `QTranslateRemake-1.1.0-linux-arch.tar.gz` — Arch build as an archive.

The AppImage and tar create `.desktop` and an icon in `~/.local/share` on first launch. The Arch package installs them system-wide.

## Requirements

- Python 3.11+;
- PySide6, requests, python-docx, pypdf — from `requirements.txt`;
- `pyenchant` — optional, for spell checking;
- system utilities — as needed.

## Install from source

```bash
git clone https://github.com/Awaynos/QTranslate-R.git
cd QTranslate-R

python3 -m venv _local/.venv
_local/.venv/bin/python -m pip install -r requirements.txt
_local/.venv/bin/python run.py
```

Install the launcher, icon and `.desktop` file:

```bash
packaging/linux/install.sh
```

The default prefix is `~/.local`. To use another prefix:

```bash
PREFIX=/usr/local packaging/linux/install.sh
```

After installation, start the app with `qtranslate-remake` or from the application menu.

## Check the environment

```bash
_local/.venv/bin/python run.py --doctor
```

It prints the session, desktop environment, XDG paths, available features and detected utilities.

## System packages

### Arch

```bash
sudo pacman -S wl-clipboard wtype tesseract grim slurp ffmpeg
sudo pacman -S tesseract-data-eng tesseract-data-rus
sudo pacman -S speech-dispatcher espeak-ng
sudo pacman -S python-pyenchant hunspell-en_us hunspell-ru
```

`ydotool` can replace `wtype`, and `mpv` can replace `ffplay`.

### Debian/Ubuntu

```bash
sudo apt install wl-clipboard wtype tesseract-ocr tesseract-ocr-eng \
  tesseract-ocr-rus grim slurp ffmpeg speech-dispatcher espeak-ng \
  python3-enchant hunspell-en-us hunspell-ru
```

### Fedora

```bash
sudo dnf install wl-clipboard wtype tesseract tesseract-langpack-eng \
  tesseract-langpack-rus grim slurp ffmpeg speech-dispatcher espeak-ng \
  python3-enchant hunspell-en hunspell-ru
```

Package names vary between distribution versions. A missing utility does not prevent the app from starting: the corresponding feature is disabled.

## Feature support

| Feature | X11 | Wayland |
|---|---|---|
| Translation, history, dictionary | yes | yes |
| Selection and replace | yes | yes, via `wl-clipboard` + `wtype`/`ydotool` |
| OCR | yes | yes, `grim` + `slurp` + `tesseract` |
| System speech | yes | yes, `spd-say`/`espeak-ng` |
| Google TTS | yes | yes, `ffplay`/`mpv`/`paplay` |
| Spell checking | yes | yes, `enchant` + Hunspell |
| Global hotkeys | automatic | desktop bindings only |
| Popup at the cursor | yes | Hyprland and some compositors |
| Tray | depends on the DE | depends on the DE |

## Global hotkeys

Linux defaults are `Ctrl+Alt+Q`, `Ctrl+Alt+1`, `Ctrl+Alt+I`, so the standard `Ctrl+Q`, `Ctrl+1`, `Ctrl+I` are not taken from other applications.

On X11 the app grabs the keys itself. Wayland forbids this, so use desktop bindings:

```bash
qtranslate-remake --quick
qtranslate-remake --replace
qtranslate-remake --ocr
```

For Hyprland the installer adds bindings and popup-position rules, backing up the config:

```bash
_local/.venv/bin/python run.py --install-hyprland-binds
```

Both `hyprland.conf` and Lua configs (including `user.lua` and `custom/keybinds.lua`) are supported.

Sway example:

```
bindsym $mod+Ctrl+q exec qtranslate-remake --quick
```

## Wayland limitations

- the app cannot position top-level windows itself; on Hyprland the popup position is set through `hyprctl` or a rule, on other compositors the compositor decides;
- global key capture requires desktop bindings or a portal;
- the GlobalShortcuts portal requires an app id; for a native app without Flatpak it is usually unavailable.

## Data locations

- from source: `_local/data`;
- installed version: `~/.local/share/QTranslate Remake` (data), `~/.config/QTranslate Remake` (settings), `~/.cache/QTranslate Remake` (cache).

## Tests

```bash
QT_QPA_PLATFORM=offscreen _local/.venv/bin/python tools/core_test.py
QT_QPA_PLATFORM=offscreen _local/.venv/bin/python tools/ocr_test.py
```

Run the OCR test without `offscreen` so fonts are rendered correctly. The full list is in `tools/`.
