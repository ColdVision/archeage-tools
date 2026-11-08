/* Общая шапка, подвал и язык сайта ArcheAge Chronicles · Tools.
   Страница задаёт <body data-root="../" data-page="trade|craft|l10n|home">, в разметке — <div id="aa-header"></div> и <div id="aa-footer"></div>.
   Язык один на весь сайт: localStorage["aa.lang"] ("ru" | "en"). Страницы-приложения слушают событие "aa-lang" на window. */
(function () {
  "use strict";
  var KEY = "aa.lang";
  var LINKS = {
    vk: "https://vk.ru/archeagechronicles",
    tg: "https://t.me/ucolda",
    yt: "https://www.youtube.com/@ycolda",
    support: "https://dalink.to/coldvision",
    repo: "https://github.com/ColdVision/ArcheAge-Chronicles-russian-translate"
  };
  var I18N = {
    ru: {
      brand: "ArcheAge Chronicles · Инструменты", tag: "Фанатские инструменты по данным игры",
      nHome: "Главная", nTrade: "Торговые маршруты", nCraft: "Калькулятор крафта", nL10n: "Локализация",
      lang: "Язык", langLabel: "Язык сайта", menu: "Меню", menuOpen: "Открыть меню разделов", menuClose: "Закрыть меню разделов",
      navLabel: "Разделы сайта", vk: "ВКонтакте: группа ArcheAge", tg: "Telegram автора", yt: "YouTube автора",
      support: "Поддержать автора", skip: "К содержимому", nojs: "Для работы сайта нужен JavaScript.",
      foot1: "Данные берутся из клиента игры ArcheAge Chronicles (таблицы и локализация); то, чего в клиенте нет (данные сервера), помечено и вводится вручную.",
      foot2: "Неофициальный фанатский проект, не связанный с издателем игры. Автор: ColdVision.",
      footLinks: "Ссылки автора"
    },
    en: {
      brand: "ArcheAge Chronicles · Tools", tag: "Fan tools built from the game data",
      nHome: "Home", nTrade: "Trade routes", nCraft: "Craft calculator", nL10n: "Localization",
      lang: "Language", langLabel: "Site language", menu: "Menu", menuOpen: "Open the section menu", menuClose: "Close the section menu",
      navLabel: "Site sections", vk: "VKontakte: ArcheAge group", tg: "Author's Telegram", yt: "Author's YouTube",
      support: "Support the author", skip: "Skip to content", nojs: "This site needs JavaScript.",
      foot1: "Data comes from the ArcheAge Chronicles client (tables and localization); anything the client does not contain (server-side data) is marked and entered by hand.",
      foot2: "Unofficial fan project, not affiliated with the game publisher. Author: ColdVision.",
      footLinks: "Author links"
    }
  };

  var lang = "ru";
  try { var v = localStorage.getItem(KEY); if (v === "ru" || v === "en") lang = v; } catch (e) {}

  var AA = window.AA = {
    LINKS: LINKS,
    get lang() { return lang; },
    t: function (k) { return (I18N[lang] && I18N[lang][k]) || I18N.ru[k] || k; },
    setLang: function (l) {
      if (l !== "ru" && l !== "en") return;
      lang = l;
      try { localStorage.setItem(KEY, l); } catch (e) {}
      document.documentElement.lang = l;
      paint();
      window.dispatchEvent(new CustomEvent("aa-lang", { detail: l }));
    },
    /* вызвать cb сразу и при каждой смене языка */
    onLang: function (cb) { cb(lang); window.addEventListener("aa-lang", function (e) { cb(e.detail); }); },
    esc: function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  };

  var body = document.body, root = body.getAttribute("data-root") || "", page = body.getAttribute("data-page") || "";
  document.documentElement.lang = lang;

  var ICON = {
    vk: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false"><rect x="1.5" y="3.5" width="21" height="17" rx="4" fill="none" stroke="currentColor" stroke-width="1.6"/><text x="12" y="16" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="9.5" fill="currentColor">VK</text></svg>',
    tg: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false"><path fill="currentColor" d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>',
    yt: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false"><path fill="currentColor" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    heart: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 21s-7.5-4.8-10-9.6C.5 8 2.4 4.5 6 4.5c2.2 0 3.7 1.2 4.6 2.6h2.8C14.3 5.7 15.8 4.5 18 4.5c3.6 0 5.5 3.5 4 6.9C19.500 16.200 12 21 12 21z"/></svg>'
  };
  var NAV = [["home", "nHome", "index.html"], ["trade", "nTrade", "trade/index.html"], ["craft", "nCraft", "craft/index.html"], ["l10n", "nL10n", "l10n/index.html"]];

  function ext(href, key, icon) {
    return '<a class="aa-ic" href="' + href + '" target="_blank" rel="noopener" aria-label="' + AA.esc(AA.t(key)) + '" title="' + AA.esc(AA.t(key)) + '">' + icon + '</a>';
  }

  function headerHtml() {
    var nav = NAV.map(function (n) {
      var cur = n[0] === page;
      return '<a href="' + root + n[2] + '"' + (cur ? ' class="cur" aria-current="page"' : '') + '>' + AA.esc(AA.t(n[1])) + '</a>';
    }).join("");
    return '<a class="aa-skip" href="#aa-main">' + AA.esc(AA.t("skip")) + '</a>' +
      '<header class="site-head"><div class="aa-bar">' +
      '<a class="aa-logo-d" href="' + root + 'index.html" aria-label="' + AA.esc(AA.t("brand")) + '" title="' + AA.esc(AA.t("brand")) + '"><img class="aa-logo" src="' + root + 'assets/logo.png" width="56" height="56" alt=""></a>' +
      '<nav class="aa-nav" id="aa-nav" aria-label="' + AA.esc(AA.t("navLabel")) + '">' + nav + '</nav>' +
      '<div class="aa-tools">' +
      '<label class="aa-lang"><span class="aa-sr">' + AA.esc(AA.t("lang")) + '</span><select id="aa-lang" aria-label="' + AA.esc(AA.t("langLabel")) + '"><option value="ru">Русский</option><option value="en">English</option></select></label>' +
      ext(LINKS.vk, "vk", ICON.vk) + ext(LINKS.tg, "tg", ICON.tg) +
      '<a class="aa-support" href="' + LINKS.support + '" target="_blank" rel="noopener">' + ICON.heart + '<span>' + AA.esc(AA.t("support")) + '</span></a>' +
      '<button type="button" class="aa-burger" id="aa-burger" aria-expanded="false" aria-controls="aa-nav" aria-label="' + AA.esc(AA.t("menuOpen")) + '"><span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span></button>' +
      '</div></header>';
  }

  function footerHtml() {
    return '<footer class="site-foot"><p>' + AA.esc(AA.t("foot1")) + '</p><p>' + AA.esc(AA.t("foot2")) + '</p>' +
      '<p class="aa-flinks" aria-label="' + AA.esc(AA.t("footLinks")) + '">' +
      '<a href="' + LINKS.yt + '" target="_blank" rel="noopener">' + ICON.yt + '<span>YouTube @ycolda</span></a>' +
      '<a href="' + LINKS.tg + '" target="_blank" rel="noopener">Telegram t.me/ucolda</a>' +
      '<a href="' + LINKS.vk + '" target="_blank" rel="noopener">' + (lang === "ru" ? "ВКонтакте" : "VK") + ' vk.ru/archeagechronicles</a>' +
      '<a href="' + LINKS.repo + '" target="_blank" rel="noopener">GitHub</a></p></footer>';
  }

  function measure() {
    var h = document.querySelector("header.site-head");
    if (h) document.documentElement.style.setProperty("--aa-head-h", h.offsetHeight + "px");
  }

  function paint() {
    var hd = document.getElementById("aa-header"), ft = document.getElementById("aa-footer");
    if (hd) hd.innerHTML = headerHtml();
    if (ft) ft.remove();
    var sel = document.getElementById("aa-lang");
    if (sel) { sel.value = lang; sel.onchange = function () { AA.setLang(sel.value); }; }
    var b = document.getElementById("aa-burger"), nav = document.getElementById("aa-nav");
    if (b && nav) {
      b.onclick = function () {
        var open = nav.classList.toggle("open");
        b.setAttribute("aria-expanded", open ? "true" : "false");
        b.setAttribute("aria-label", AA.t(open ? "menuClose" : "menuOpen"));
        measure();
      };
    }
    measure();
  }

  var ro = window.ResizeObserver ? new ResizeObserver(measure) : null;
  function watch() { var hh = document.querySelector("header.site-head"); if (ro && hh) { ro.disconnect(); ro.observe(hh); } }
  window.addEventListener("resize", measure);
  window.addEventListener("load", measure);
  paint();
  watch();
  document.addEventListener("DOMContentLoaded", function () { watch(); measure(); });
  window.addEventListener("aa-lang", watch);
})();
