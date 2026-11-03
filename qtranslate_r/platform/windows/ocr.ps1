param(
    [string]$ImagePath = "",
    [string]$Language = "",
    [string]$OutputPath = "",
    [switch]$ListLanguages
)

$ErrorActionPreference = "Stop"

function Write-Json($Value) {
    $json = $Value | ConvertTo-Json -Compress -Depth 4
    if ($OutputPath) {
        [System.IO.File]::WriteAllText($OutputPath, $json, (New-Object System.Text.UTF8Encoding($false)))
    } else {
        [Console]::Out.Write($json)
    }
}

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq "AsTask" -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq "IAsyncOperation``1"
    })[0]

    function Await($Operation, $Type) {
        $task = $asTask.MakeGenericMethod($Type).Invoke($null, @($Operation))
        $task.Wait(-1) | Out-Null
        $task.Result
    }

    [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
    [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null

    if ($ListLanguages) {
        Write-Json @{
            ok        = $true
            languages = @([Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | ForEach-Object { $_.LanguageTag })
        }
        exit 0
    }

    $lang = New-Object Windows.Globalization.Language($Language)
    if (-not [Windows.Media.Ocr.OcrEngine]::IsLanguageSupported($lang)) {
        Write-Json @{
            ok        = $false
            error     = "unsupported_language"
            languages = @([Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | ForEach-Object { $_.LanguageTag })
        }
        exit 0
    }

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
    if ($null -eq $engine) {
        Write-Json @{ ok = $false; error = "no_engine" }
        exit 0
    }

    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $ocr = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $lines = @($ocr.Lines | ForEach-Object { $_.Text })
        Write-Json @{
            ok       = $true
            text     = [string]::Join("`n", $lines)
            language = $engine.RecognizerLanguage.LanguageTag
        }
    } finally {
        if ($stream) { $stream.Dispose() }
    }
} catch {
    Write-Json @{ ok = $false; error = $_.Exception.Message }
}
