# Публикация сайта на GitHub Pages (ветка main, корень репозитория = папка Site).
# По умолчанию — только проверка (dry-run): считает файлы и размер, проверяет лимиты Pages и запрещённое содержимое,
# проверяет относительные ссылки, показывает план. НИЧЕГО не отправляет, репозитории не создаёт.
# Реальная отправка — только с -Publish и подтверждением ДА.
#   powershell -ExecutionPolicy Bypass -File tools\publish_site.ps1 -Repo ВАШ_ЛОГИН/archeage-tools
#   powershell -ExecutionPolicy Bypass -File tools\publish_site.ps1 -Repo ВАШ_ЛОГИН/archeage-tools -Publish
param(
    [string]$Repo = '',             # владелец/имя репозитория, например ColdVision/archeage-tools
    [switch]$Publish,
    [switch]$Yes                    # подтверждение уже получено в чате: не спрашивать ДА
)
$ErrorActionPreference = 'Stop'
$site = Split-Path $PSScriptRoot -Parent
$files = Get-ChildItem $site -Recurse -File -Force | Where-Object { $_.FullName -notlike '*\.git\*' -and $_.FullName -notlike '*__pycache__*' }
$total = ($files | Measure-Object Length -Sum).Sum
"Сайт: $site"
"Файлов: $($files.Count), размер: $([math]::Round($total / 1MB, 1)) МБ (лимит Pages: сайт 1 ГБ, файл 100 МБ)"
$bad = @()
foreach ($f in $files) {
    $rel = $f.FullName.Substring($site.Length + 1)
    if ($f.Length -gt 90MB) { $bad += "файл больше 90 МБ: $rel" }
    if ($f.Extension -match '^\.(locres|pak|utoc|ucas|usmap|x5tr|exe|dll)$') { $bad += "файл игры/бинарник: $rel" }
    if ($f.Extension -match '^\.(js|json|html|py|ps1|md|css|txt)$') {
        $txt = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($txt -match '(?i)\baes\s*[_-]?key\b\s*["'':= ]+\s*(0x)?[0-9a-f]{32,}') { $bad += "похоже на AES-ключ: $rel" }
        if ($f.Extension -match '^\.(html|js)$' -and $txt -match '(src|href)\s*=\s*["'']/(?!/)') { $bad += "абсолютный путь (сломается на Pages): $rel" }
    }
}
foreach ($need in 'index.html', '404.html', '.nojekyll', 'robots.txt', 'trade\index.html', 'craft\index.html', 'l10n\index.html', 'data\news.json') {
    if (-not (Test-Path (Join-Path $site $need))) { $bad += "нет файла: $need" }
}
if ($bad.Count) { 'ПРОБЛЕМЫ (отправка запрещена):'; $bad | ForEach-Object { "  - $_" }; exit 1 }
'Проверка: OK (лимиты, нет файлов игры/ключей, нет абсолютных путей, обязательные файлы на месте).'
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source; $git = (Get-Command git -ErrorAction SilentlyContinue).Source
"gh: $(if ($gh) { $gh } else { 'не установлен' }); git: $(if ($git) { $git } else { 'не установлен' })"
if (-not $Publish) {
    ''
    "План при -Publish: git init в временной копии, коммит всех файлов, push в https://github.com/$(if ($Repo) { $Repo } else { '<владелец/репозиторий>' }) (ветка main), включение Pages (main, /root)."
    'DRY-RUN: ничего не отправлено.'
    exit 0
}
if (-not $Repo) { throw 'Укажите -Repo владелец/имя.' }
if (-not $gh -or -not $git) { throw 'Нужны GitHub CLI (gh) и git.' }
& $gh auth status *> $null; if ($LASTEXITCODE) { throw 'gh не авторизован: выполните gh auth login.' }
if (-not $Yes) { $a = Read-Host "Отправить сайт в $Repo и включить Pages? Введите ДА"; if ($a -ne 'ДА') { 'Отменено.'; exit 0 } }
$ErrorActionPreference = 'Continue'
& $gh repo view $Repo *> $null
$exists = ($LASTEXITCODE -eq 0)
if (-not $exists) {
    if (-not $Yes) { $a2 = Read-Host "Репозиторий $Repo не найден. Создать публичный? Введите ДА"; if ($a2 -ne 'ДА') { 'Отменено.'; exit 0 } }
    & $gh repo create $Repo --public --description 'ArcheAge Chronicles: инструменты и перевод'; if ($LASTEXITCODE) { throw 'не удалось создать репозиторий' }
}
$ErrorActionPreference = 'Stop'
$stage = Join-Path $env:TEMP "aa-site-$([guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory $stage | Out-Null
robocopy $site $stage /E /XD __pycache__ .git /NFL /NDL /NJH /NJS | Out-Null
Push-Location $stage
try {
    & $git init -b main | Out-Null
    & $git add -A; & $git commit -m 'Сайт ArcheAge Chronicles: инструменты и перевод' | Out-Null
    & $git remote add origin "https://github.com/$Repo.git"
    & $git push -u origin main; if ($LASTEXITCODE) { throw 'git push не удался (если в репозитории уже есть история — слейте её вручную)' }
    & $gh api -X POST "repos/$Repo/pages" -f 'source[branch]=main' -f 'source[path]=/' 2>$null | Out-Null
    "Готово. Адрес появится через 1–2 минуты: https://$($Repo.Split('/')[0].ToLower()).github.io/$($Repo.Split('/')[1])/"
} finally { Pop-Location; Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
