# ArcheAge Chronicles · Инструменты (сайт для GitHub Pages)

Статический сайт без сервера и сборки: главная (новости, патчи, состояние перевода), торговые маршруты, калькулятор крафта, локализация (русский перевод). Корень этой папки = корень сайта, все пути относительные, сайт работает офлайн и по http. Язык (Русский / English) общий для всего сайта: `localStorage["aa.lang"]`. Стиль — «Academia» (`assets/aa-theme.css`, токены и шрифты не менять).

## Структура
```
index.html            главная: последний патч, лента новостей/патчей (фильтр), состояние перевода
trade\index.html      торговые маршруты (карта мира)
craft\index.html      калькулятор крафта
l10n\index.html       локализация: версии A/B, установка, скачивание, охват, контрольные суммы
404.html  robots.txt  .nojekyll
assets\               aa-theme.css, site.css, site.js (шапка, подвал, язык), release.js (GitHub API)
                      trade\ (карта, иконки), craft\icons\
data\                 news.json + news.js, translation.json + translation.js,
                      trade\ (tradedata, roads), craft\ (craftdata, crafting, recipes), manual — ручные данные
tools\                скрипты пересборки данных (пишут прямо в data\ и assets\ этого сайта)
```

## Как выложить на GitHub Pages
1. Создайте репозиторий на GitHub (например `archeage-tools`, публичный).
2. Загрузите в него **содержимое папки Site** (чтобы `index.html` лежал в корне репозитория).
   Либо скриптом: `powershell -ExecutionPolicy Bypass -File tools\publish_site.ps1 -Repo ЛОГИН/archeage-tools` — по умолчанию только проверка (dry-run), с `-Publish` отправит сайт после вашего подтверждения «ДА» (нужны `git` и `gh auth login`).
3. Репозиторий → **Settings → Pages → Build and deployment → Source: Deploy from a branch**, ветка `main`, папка `/ (root)` → Save.
4. Через 1–2 минуты сайт откроется по адресу `https://ЛОГИН.github.io/archeage-tools/`. Файл `.nojekyll` отключает обработку Jekyll.

Лимиты Pages: сайт до 1 ГБ, файл до 100 МБ, около 100 ГБ трафика в месяц. Сейчас сайт весит около 9 МБ.

## Как обновить данные после патча игры
Нужна распакованная таблица игры (CMS) и русский перевод проекта; AES-ключ берётся из `%APPDATA%\X5Viewer\settings.json` во время работы и **никуда не записывается**.
- Таблицы игры: `powershell -File tools\craft\extract_cms.ps1 -Build НОМЕР_СБОРКИ`.
- Торговые маршруты: `python tools\trade\build_data.py --cms … --locres … --build …`; иконки `tools\trade\build_icons.py`; карта `tools\trade\build_map.py`; дороги `tools\trade\build_roads.py`.
- Крафт: `python tools\craft\build_data.py …`, затем `tools\craft\build_crafting.py`, иконки `tools\craft\build_icons.py`.
- Перевод: после нового релиза `python tools\build_translation_info.py` обновит `data\translation.json/.js` (запасной снимок для страниц «Главная» и «Локализация»; живые данные страницы берут из GitHub API).
- Новости и патчи: `python tools\add_news.py` (интерактивно) или с аргументами, см. ниже.
Скрипты пересчитывают пути от своего расположения: они пишут в `data\trade`, `data\craft`, `assets\trade`, `assets\craft` этого сайта.

## Как добавить новость или патч
Данные лежат в `data\news.json` (схема — в поле `_schema` файла). Запись:
`id`, `date` (ГГГГ-ММ-ДД), `type` (`news` или `patch`), `title` и `text` (`ru`/`en`), `version`, `build`, `url`, `sample` (true — пробная запись, на сайте помечается «пример»).
Проще всего скриптом, он обновляет и `news.json`, и копию `news.js` (нужна для открытия без сервера):
```
python tools\add_news.py --type patch --date 2026-11-20 --version 1.2.3 --build 26500000 --title-ru "Обновление 1.2.3" --title-en "Update 1.2.3" --text-ru "Исправления." --text-en "Fixes." --url https://…
python tools\add_news.py --drop-samples      # удалить пробные записи
```
Если правили `news.json` руками, выполните `python toolsdd_news.py --sync` — он пересоздаст `news.js`.

### Импорт постов ВКонтакте через API
`python tools/import_vk_news.py` забирает посты группы (wall.get) и добавляет их в `news.json` с пометкой VK и ссылкой на пост. Нужен токен: сервисный ключ приложения ВК (vk.com/apps?act=manage → Standalone-приложение). Положите его в переменную `VK_TOKEN` или в файл `%APPDATA%a-sitek_token.txt` (вне папки сайта). Токен нельзя вставлять в страницы сайта: он стал бы публичным, поэтому лента обновляется скриптом перед выкладкой. Режим `--dry-run` только показывает посты.

## Данные и источники
Основа — клиент игры (CMS-таблицы, локализация, текстуры). Чего в клиенте нет (экономика торговых товаров, часть рецептов крафта — данные сервера), лежит в `data\*\source\` и помечено в соответствующих разделах; эти файлы собраны вручную/по сторонним справочникам (`trade-goods.json`, `recipes-manual.json`, `materials-manual.json`), см. `README` исходных проектов. Решите, оставлять ли их на публичном сайте.

## Ссылки
Telegram автора https://t.me/ucolda · ВКонтакте https://vk.ru/archeagechronicles · YouTube https://www.youtube.com/@ycolda · Поддержать https://dalink.to/coldvision · Перевод https://github.com/ColdVision/ArcheAge-Chronicles-russian-translate
