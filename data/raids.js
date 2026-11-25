/* Расписание рейдов ArcheAge Chronicles. Время начала — UTC, каждый день. Источник: новость Steam от 20.11.2026.
   Чтобы поправить расписание, измените массивы times (часы:минуты UTC) и длительность dur (минуты). */
window.AA_RAIDS = {
  updated: "2026-11-25",
  source: "https://store.steampowered.com/news/app/3218230/view/707789068701794653",
  raids: [
    { id: "crimson", ru: "Багровый Разлом", en: "Crimson Rift", times: ["03:00", "11:00", "19:00"], dur: 30, difficulty: "normal" },
    { id: "crimson-hard", ru: "Багровый Разлом", en: "Crimson Rift", times: ["03:30", "11:30", "19:30"], dur: 30, difficulty: "hard" },
    { id: "nightmare", ru: "Жестокий Кельтак", en: "Brutal Nightmare", times: ["04:00", "12:00", "20:00"], dur: 60, difficulty: "normal" },
    { id: "nightmare-hard", ru: "Жестокий Кельтак", en: "Brutal Nightmare", times: ["05:00", "13:00", "21:00"], dur: 60, difficulty: "hard" }
  ]
};
