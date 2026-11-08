/* Последний релиз перевода: GitHub API в браузере, при ошибке — снимок data/translation.js (tools/build_translation_info.py).
   AARelease.get() -> Promise<{source:"api"|"snapshot", version, tag, date, build, url, assets:[{name,size,url}], snap}> */
(function () {
  "use strict";
  var REPO = "ColdVision/ArcheAge-Chronicles-russian-translate";
  var API = "https://api.github.com/repos/" + REPO + "/releases/latest";
  var CK = "aa.release.cache", TTL = 10 * 60 * 1000;
  function snapshot() {
    var s = window.AA_TRANSLATION; if (!s) return null;
    return {
      source: "snapshot", version: s.version, tag: s.tag, date: s.built_utc, build: s.game_build,
      url: "https://github.com/" + REPO + "/releases/latest",
      assets: (s.files || []).map(function (f) { return { name: f.name, size: f.size, url: s.download_base + f.name }; }), snap: s
    };
  }
  function parse(j) {
    var m = /build\s*id\s*:?\s*(\d{5,})/i.exec(j.body || "") || /(?:сборк[аи]\D{0,30}|build\D{0,10})(\d{7,9})/i.exec(j.body || "");
    var snap = window.AA_TRANSLATION || null;
    var ver = String(j.tag_name || "").replace(/^v/i, "");
    return {
      source: "api", version: ver, tag: j.tag_name, date: j.published_at,
      build: m ? m[1] : (snap && snap.version === ver ? snap.game_build : null),
      url: j.html_url, snap: snap && snap.version === ver ? snap : null,
      assets: (j.assets || []).map(function (a) { return { name: a.name, size: a.size, url: a.browser_download_url }; })
    };
  }
  function get() {
    try { var c = JSON.parse(sessionStorage.getItem(CK) || "null"); if (c && Date.now() - c.t < TTL) return Promise.resolve(c.v); } catch (e) {}
    return new Promise(function (resolve) {
      var done = false;
      function fail() { if (done) return; done = true; resolve(snapshot()); }
      var timer = setTimeout(fail, 7000);
      try {
        fetch(API, { headers: { Accept: "application/vnd.github+json" } }).then(function (r) {
          if (!r.ok) throw new Error(r.status); return r.json();
        }).then(function (j) {
          if (done) return; done = true; clearTimeout(timer);
          var v = parse(j);
          try { sessionStorage.setItem(CK, JSON.stringify({ t: Date.now(), v: v })); } catch (e) {}
          resolve(v);
        }).catch(function () { clearTimeout(timer); fail(); });
      } catch (e) { clearTimeout(timer); fail(); }
    });
  }
  window.AARelease = { get: get, REPO: REPO, latestPage: "https://github.com/" + REPO + "/releases/latest", issues: "https://github.com/" + REPO + "/issues" };
})();
