# Извлекает CMS-таблицы и строки локализации из X5-Windows.pak в новую папку выгрузки (после патча).
# AES-ключ берётся из %APPDATA%\X5Viewer\settings.json в момент запуска, в файлы проекта НЕ пишется.
# Игровая папка только читается.
#
#   powershell -ExecutionPolicy Bypass -File tools\extract_cms.ps1 -Build 26500000
#   python tools\build_data.py --cms D:\Claude\aa-tools\game-data-26500000\X5\Content\Design\CMS `
#          --locres D:\Claude\aa-tools\game-data-26500000\X5\Content\Localization\String\en\String.locres --build 26500000
param(
  [Parameter(Mandatory = $true)][string]$Build,
  [string]$Out = "",
  [string]$X5Pakx = "D:\Claude\aa-tools\X5Pakx\bin\Release\net10.0\x5pakx.exe"
)
$ErrorActionPreference = "Stop"
$s = Get-Content "$env:APPDATA\X5Viewer\settings.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $s.AesKey -or -not $s.GameDir) { throw "В settings.json X5Viewer нет AesKey/GameDir" }
if (-not $Out) { $Out = "D:\Claude\aa-tools\game-data-$Build" }
if (-not (Test-Path $X5Pakx)) { $X5Pakx = (Get-ChildItem "D:\Claude\aa-tools\X5Pakx\bin" -Recurse -Filter x5pakx.exe | Select-Object -First 1).FullName }
$pak = Join-Path $s.GameDir "X5-Windows.pak"
$args2 = @($pak, $s.AesKey, $Out, "(Localization/.*\.(locres|locmeta)$|/Design/CMS/)")
if ($s.OodlePath -and (Test-Path $s.OodlePath)) { $args2 += $s.OodlePath }
& $X5Pakx @args2
Write-Host "Готово: $Out"
