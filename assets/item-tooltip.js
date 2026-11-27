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

  const equipmentPercent = new Set(["MaxSP","PhysicalArmor","MagicArmor","HitArmor"]);
  const russianStats = {
    MaxSP:"Макс. выносливость", MaxHP:"Макс. здоровье", PhysicalArmor:"Физ. защита", MagicArmor:"Маг. защита",
    HitArmor:"Сопр. ошеломлению", HitAttackPower:"Ошеломление", ImpactAttackPower:"Истощение",
    PhysicalAttackPower:"Физ. атака", MagicAttackPower:"Маг. атака", PhysicalCritical:"Рейтинг физ. крита",
    MagicCritical:"Рейтинг маг. крита", MagicCriticalRateInc:"Шанс маг. крита", PhysicalCriticalRateInc:"Шанс физ. крита",
    PhysicalCriticalPowerInc:"Урон физ. крита", MagicCriticalPowerInc:"Урон маг. крита",
    PhysicalIgnoreArmor:"Пробивание физ. защиты", MagicIgnoreArmor:"Пробивание маг. защиты",
    MoveSpeedRate:"Скорость движения", PotionHealRate:"Сила зелий", NormalNpcDamageInc:"Урон по обычным монстрам",
    FogArmor:"Защита от тумана", FogAttackPower:"Атака туманом", IronArmor:"Защита от стали", IronAttackPower:"Атака сталью",
    ElectricArmor:"Защита от молнии", ElectricAttackPower:"Атака молнией", FireArmor:"Защита от огня", FireAttackPower:"Атака огнём",
    WindArmor:"Защита от ветра", WindAttackPower:"Атака ветром", TidalArmor:"Защита от прилива", TidalAttackPower:"Атака приливом",
    Tal:"Талант"
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
    const word = (r, e) => ru ? r : e;
    const number = n => Number(n).toLocaleString(ru ? "ru-RU" : "en-GB");
    const data = window.CRAFT_ITEM_DETAILS?.[it.id] || {};
    const slotNames = {
      ArmorHelmet:["Шлем","Helmet"], ArmorSuit:["Доспех","Chest armor"], ArmorShoes:["Сапоги","Boots"],
      ArmorGloves:["Перчатки","Gloves"], Bracelet:["Браслет","Bracelet"], Earring:["Серьга","Earring"],
      Necklace:["Ожерелье","Necklace"], Ring:["Кольцо","Ring"], Bag:["Сумка","Bag"], FlightTool:["Планер","Glider"],
      CostumeCloak:["Плащ","Cloak"], CostumeGlasses:["Очки","Glasses"], CostumeGloves:["Перчатки","Gloves"],
      CostumeHelmet:["Головной убор","Headwear"], CostumeShoes:["Обувь","Shoes"], CostumeSuit:["Костюм","Costume"]
    };
    const slot = slotNames[data.equipSlot];
    const armor = data.equipSlot?.startsWith("Armor");
    const category = armor ? word("Броня","Armor") : (ru ? CAT[it.cat] || it.cat : it.cat.replace(/([a-z])([A-Z])/g,"$1 $2"));
    const material = {Metal:word("Металл","Metal"),Leather:word("Кожа","Leather"),Fabric:word("Ткань","Fabric")}[data.equipMaterial];
    const grade = grades[it.grade]?.[ru ? 0 : 1] || it.grade;
    const desc = ru ? it.dru || it.den : it.den || it.dru;
    const pill = (v,c="") => v ? '<span class="tip-pill '+c+'">'+h(v)+'</span>' : "";
    const price = (label,value,type) => value > 0 ? '<span>'+label+' <b title="'+h(type)+'">'+(type==="Gold" ? '<i class="tip-coin">G</i>' : h(type)+' ')+number(value)+'</b></span>' : "";
    const prices = price(word("Цена","Price"),it.price,it.pt)+price(word("Продажа","Sells for"),data.refundValue,data.refundType);
    const equipment = window.CRAFT_EQUIPMENT_STATS;
    const entry = equipment?.items[it.id] || {};
    const stone = items.get(entry.stone);
    const statLabel = code => ru ? russianStats[code] || equipment.labels[code].en : equipment.labels[code].en;
    const stats = (entry.stats || []).map(([code, raw]) => {
      const label = equipment.labels[code];
      // QuestLog's equipment card displays these four ratings as percentages.
      const pattern = equipmentPercent.has(code) ? "{0}%" : label.format;
      const value = pattern.replace("{0}",number(raw * label.multiplier));
      const icon = label.icon ? '<img alt="" src="../assets/craft/tooltip/'+h(label.icon)+'.png">' : '<i class="tip-stat-mark" aria-hidden="true"></i>';
      return '<div>'+icon+'<span><b>'+h(value)+'</b><small>'+h(statLabel(code))+'</small></span></div>';
    }).join("");
    const requirements = (entry.requirements || []).map(([code,v]) => h(statLabel(code))+' '+number(v)).join(" · ");
    const sockets = (entry.chances || []).map(([count,chance]) =>
      pill(word("Ячеек: ","Sockets: ")+number(count)+" · "+number(chance)+"%")).join(" ");
    const openChance = entry.openChance ? pill(word("Шанс открытия: ","Open chance: ")+number(entry.openChance)+"%") : "";
    card.dataset.grade = it.grade;
    card.innerHTML = '<div class="tip-head">'+
      (it.ic ? '<img class="tip-art" alt="" src="../assets/craft/'+(it.ic === 12602102 ? "tooltip/" : "icons/")+Number(it.ic)+'.png">' : '')+
      '<strong>'+h(nm(it.id))+'</strong><div class="tip-type">'+h(slot ? '['+category+'] '+slot[ru?0:1] : category)+'</div>'+
      '<div class="tip-badges">'+pill(grade,"quality")+pill(material)+pill(it.className && classLabel(it.className))+'</div>'+
      ((data.maxDurability || data.weight) ? '<div class="tip-measures">'+
        (data.maxDurability ? '<span>'+word("Прочность","Durability")+' <b>'+number(data.maxDurability)+'</b></span>' : '')+
        (data.weight ? '<span>'+word("Вес","Weight")+' <b>'+number(data.weight/1000)+'</b></span>' : '')+'</div>' : '')+'</div>'+
      (desc ? '<p class="tip-desc">'+h(desc)+'</p>' : '')+
      (stats ? '<div class="tip-stats">'+stats+'</div>' : '')+
      (it.lvl ? '<div class="tip-level">'+word("Уровень","Level")+'<b>'+number(it.lvl)+'</b></div>' : '')+
      (requirements ? '<div class="tip-level">'+word("Требования","Requirements")+'<b>'+requirements+'</b></div>' : '')+
      ((sockets || stone || openChance || entry.shape) ? '<div class="tip-sockets"><small>'+word("Ячейки самоцветов","Lunagem sockets")+'</small>'+sockets+openChance+
        (entry.shape ? pill(entry.shape) : '')+(stone ? '<div>'+(stone.ic ? '<img alt="" src="../assets/craft/icons/'+Number(stone.ic)+'.png">' : '')+h(nm(stone.id))+'</div>' : '')+'</div>' : '')+
      (prices ? '<div class="tip-prices">'+prices+'</div>' : '');
    el.setAttribute("aria-describedby",card.id);
    card.hidden = false; card.scrollTop = 0;
    const rect = el.getBoundingClientRect(), gap = 5;
    const width = document.documentElement.clientWidth, w = card.offsetWidth, ht = card.offsetHeight;
    const rightFits = rect.right + gap + w <= width - 8;
    const leftFits = rect.left - gap - w >= 8;
    const left = rightFits ? rect.right + gap : leftFits ? rect.left - gap - w : Math.max(8, Math.min(rect.left,width-w-8));
    const top = rightFits || leftFits ? rect.top : rect.bottom+gap+ht <= innerHeight-8 ? rect.bottom+gap : rect.top-gap-ht;
    card.style.left = left + "px";
    card.style.top = Math.max(8,Math.min(top,innerHeight-card.offsetHeight-8)) + "px";
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
