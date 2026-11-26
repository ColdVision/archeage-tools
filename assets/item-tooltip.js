(() => {
  const selector = "[data-i], [data-nd], [data-resource]";
  const card = document.createElement("div");
  card.className = "item-tip";
  card.id = "craft-item-info";
  card.setAttribute("role", "tooltip");
  card.hidden = true;
  document.body.appendChild(card);
  let anchor = null, closing = 0;
  const grades = {
    Normal:["Обычный","Common"], Grand:["Необычный","Uncommon"], Rare:["Редкий","Rare"],
    Heroic:["Эпический","Epic"], Legendary:["Легендарный","Legendary"]
  };

  function hide() {
    clearTimeout(closing);
    if (anchor) anchor.removeAttribute("aria-describedby");
    anchor = null;
    card.hidden = true;
  }
  function delayedHide() { clearTimeout(closing); closing = setTimeout(hide, 180); }
  function show(el) {
    if (!el) return;
    clearTimeout(closing);
    const it = items.get(Number(el.dataset.i || el.dataset.nd || el.dataset.resource));
    if (!it) return;
    if (anchor && anchor !== el) anchor.removeAttribute("aria-describedby");
    anchor = el;
    const ru = S.lang === "ru";
    const category = ru ? (CAT[it.cat] || it.cat) : it.cat.replace(/([a-z])([A-Z])/g,"$1 $2");
    const fields = [category, grades[it.grade]?.[ru ? 0 : 1] || it.grade,
      it.className && classLabel(it.className)];
    if (it.lvl) fields.push((ru ? "Ур. " : "Lv. ") + it.lvl);
    const desc = ru ? it.dru || it.den : it.den || it.dru;
    card.innerHTML = '<strong class="gr-' + h(it.grade) + '">' + h(nm(it.id)) +
      '</strong><div class="attributes">' + fields.filter(Boolean).map(h).join(" · ") + "</div>" +
      (desc ? "<p>" + h(desc) + "</p>" : "");
    el.setAttribute("aria-describedby",card.id);
    card.hidden = false;
    const rect = el.getBoundingClientRect(), gap = 5;
    const left = Math.max(8,Math.min(rect.left,document.documentElement.clientWidth-card.offsetWidth-8));
    const top = rect.bottom+gap+card.offsetHeight < innerHeight ? rect.bottom+gap : rect.top-gap-card.offsetHeight;
    card.style.left = left + "px";
    card.style.top = Math.max(8,top) + "px";
  }
  document.addEventListener("pointerover", e => {
    if (e.pointerType === "touch") return;
    if (card.contains(e.target)) { clearTimeout(closing); return; }
    const el = e.target.closest(selector);
    if (el && el !== anchor) show(el);
    else if (el) clearTimeout(closing);
  });
  document.addEventListener("pointerout", e => {
    if ((anchor?.contains(e.target) || card.contains(e.target)) &&
        !anchor?.contains(e.relatedTarget) && !card.contains(e.relatedTarget)) delayedHide();
  });
  document.addEventListener("focusin", e => show(e.target.closest(selector)));
  document.addEventListener("focusout", e => { if(anchor?.contains(e.target)) delayedHide(); });
  document.addEventListener("pointerdown", e => {
    if (!card.contains(e.target) && !e.target.closest(selector)) hide();
  });
  document.addEventListener("click", e => {
    if (e.pointerType !== "touch") return;
    const el = e.target.closest(selector);
    if (!el) return;
    const key = ["i","nd","resource"].find(k => el.dataset[k]);
    // A selection can replace the clicked row before this event bubbles.
    const next = el.isConnected ? el : document.querySelector('[data-'+key+'="'+el.dataset[key]+'"]');
    show(next);
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") hide(); });
  document.addEventListener("scroll", e => { if(e.target !== card) hide(); },true);
  new MutationObserver(() => { if (anchor && !anchor.isConnected) hide(); })
    .observe(document.getElementById("aa-main"), {childList:true, subtree:true});
  window.addEventListener("resize", hide);
  window.addEventListener("aa-lang", hide);
})();
