/* Расписание рейдов ArcheAge Chronicles. Время начала — UTC, каждый день. Источник: новость Steam от 20.11.2026.
   Чтобы поправить расписание, измените массивы times (часы:минуты UTC) и длительность dur (минуты). */
window.AA_RAIDS = {
  updated: "2026-11-20",
  source: "https://store.steampowered.com/news/app/3218230/view/707789068701794653",
  raids: [
    { id: "crimson", ru: "Багровая расщелина", en: "Crimson Rift", times: ["03:00", "11:00", "19:00"], dur: 30, hard: true },
    { id: "nightmare", ru: "Жестокий кошмар", en: "Brutal Nightmare", times: ["04:00", "12:00", "20:00"], dur: 30, hard: true }
  ]
};
