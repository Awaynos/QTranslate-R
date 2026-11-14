# QTranslate Remake на Linux

Приложение работает из исходников и поддерживает X11 и Wayland. Часть функций зависит от окружения и установленных утилит.

## Требования

- Python 3.11+;
- PySide6, requests, python-docx, pypdf — из `requirements.txt`;
- `pyenchant` — опционально, для орфографии;
- системные утилиты — по необходимости.

## Установка из исходников

```bash
git clone https://github.com/Awaynos/QTranslate-R.git
cd QTranslate-R

python3 -m venv _local/.venv
_local/.venv/bin/python -m pip install -r requirements.txt
_local/.venv/bin/python run.py
```

Установка ярлыка, иконки и `.desktop`:

```bash
packaging/linux/install.sh
```

По умолчанию ставится в `~/.local`. Другой префикс:

```bash
PREFIX=/usr/local packaging/linux/install.sh
```

После установки приложение запускается командой `qtranslate-remake` или из меню приложений.

## Проверка окружения

```bash
_local/.venv/bin/python run.py --doctor
```

Показывает сессию, DE, пути XDG, доступные функции и найденные утилиты.

## Системные пакеты

### Arch

```bash
sudo pacman -S wl-clipboard wtype tesseract grim slurp ffmpeg
sudo pacman -S tesseract-data-eng tesseract-data-rus
sudo pacman -S speech-dispatcher espeak-ng
sudo pacman -S python-pyenchant hunspell-en_us hunspell-ru
```

`ydotool` можно использовать вместо `wtype`, `mpv` — вместо `ffplay`.

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

Названия пакетов могут отличаться между версиями дистрибутивов. Отсутствие утилиты не мешает запуску: соответствующая функция просто отключается.

## Что работает где

| Функция | X11 | Wayland |
|---|---|---|
| Перевод, история, словарь | да | да |
| Выделение и замена | да | да, через `wl-clipboard` + `wtype`/`ydotool` |
| OCR | да | да, `grim` + `slurp` + `tesseract` |
| Системная озвучка | да | да, `spd-say`/`espeak-ng` |
| Google TTS | да | да, `ffplay`/`mpv`/`paplay` |
| Орфография | да | да, `enchant` + Hunspell |
| Глобальные хоткеи | автоматически | только бинды DE |
| Позиция попапа у курсора | да | Hyprland и некоторые композиторы |
| Трей | зависит от DE | зависит от DE |

## Глобальные хоткеи

На Linux по умолчанию используются `Ctrl+Alt+Q`, `Ctrl+Alt+1`, `Ctrl+Alt+I`, чтобы не отбирать стандартные `Ctrl+Q`, `Ctrl+1`, `Ctrl+I` у других приложений.

На X11 приложение само перехватывает клавиши. На Wayland это запрещено, поэтому нужны бинды окружения:

```bash
qtranslate-remake --quick
qtranslate-remake --replace
qtranslate-remake --ocr
```

Для Hyprland установщик сам добавит бинды и правила позиции попапа, сделав бэкап конфига:

```bash
_local/.venv/bin/python run.py --install-hyprland-binds
```

Для `hyprland.conf` и Lua-конфигов (включая `user.lua` и `custom/keybinds.lua`) поддерживаются оба формата.

Пример для Sway:

```
bindsym $mod+Ctrl+q exec qtranslate-remake --quick
```

## Ограничения Wayland

- приложение не может само позиционировать top-level окна; на Hyprland позиция попапа задаётся через `hyprctl` или правило, в других композиторах её выбирает композитор;
- глобальный перехват клавиш недоступен без биндов DE или портала;
- портал GlobalShortcuts требует app id; для нативного запуска без Flatpak он обычно недоступен.

## Где лежат данные

- из исходников: `_local/data`;
- установленная версия: `~/.local/share/QTranslate Remake` (данные), `~/.config/QTranslate Remake` (настройки), `~/.cache/QTranslate Remake` (кеш).

## Тесты

```bash
QT_QPA_PLATFORM=offscreen _local/.venv/bin/python tools/core_test.py
QT_QPA_PLATFORM=offscreen _local/.venv/bin/python tools/ocr_test.py
```

OCR-тест лучше запускать без `offscreen`, чтобы шрифты рисовались корректно. Полный список — в `tools/`.
