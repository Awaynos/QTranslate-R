# Сборка QTranslate Remake в один .exe
#
# Требуется PyInstaller в окружении проекта:
#   _local\.venv\Scripts\python.exe -m pip install pyinstaller
#
# Запуск:  powershell -ExecutionPolicy Bypass -File packaging\build.ps1
#
# Окружение, сборка и результат складываются в _local — в репозиторий не попадают.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root "_local\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Не найдено окружение _local\.venv. Создайте его и установите зависимости."
}

$local = Join-Path $root "_local"

& $python -m PyInstaller `
    --noconfirm --clean --onefile --windowed `
    --name QTranslateRemake `
    --icon "$root\packaging\app.ico" `
    --version-file "$root\packaging\version_info.txt" `
    --add-data "$root\languages;languages" `
    --add-data "$root\icons;icons" `
    --add-data "$root\qtranslate_r\platform\ocr.ps1;qtranslate_r\platform" `
    --add-data "$root\VERSION;." `
    --workpath "$local\build" `
    --distpath "$local\dist" `
    --specpath "$local" `
    "$root\run.py"

Write-Host ""
Write-Host "Готово: _local\dist\QTranslateRemake.exe"
Write-Host "Настройки и история будут в %APPDATA%\QTranslate Remake."

