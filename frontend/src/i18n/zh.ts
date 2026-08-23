import type { Dictionary } from "./types";

export const zh: Dictionary = {
  switchLangLabel: "EN",
  switchLangAriaLabel: "切換語言",
  localeNames: {
    zh: "中文",
    en: "English",
  },

  appTitle: "旅遊行前天氣規劃",
  appTagline: "選擇目的地後即可查看一週天氣、未來 72 小時趨勢與行前提醒。",
  loadingTowns: "載入鄉鎮清單中…",
  queryFailed: "查詢失敗",
  queryFailedDefault: "查詢失敗，請稍後再試。",
  footerNote: "出發前先看一眼天氣與日照資訊，行程安排更從容。",

  labelCity: "縣市",
  labelTown: "鄉鎮市區",
  btnQuerying: "查詢中…",
  btnQuery: "查詢天氣",

  hourlyChartTitle: "72 小時逐 3 小時預報",
  hourlyChartSubtitle: "雙曲線為氣溫與體感溫度，底部藍柱為各時段降雨機率。",
  legendTemp: "氣溫",
  legendApparentTemp: "體感溫度",
  hourlyChartAriaLabel: "72 小時逐 3 小時溫度與降雨機率圖",
  hourlyChartNote: "體感溫度資料不足時會略過紫色曲線，不影響其他時段資訊。",

  sunAstroRef: (date: string) => `參考 ${date} 天文資料`,
  uvObserved: "觀測值",
  uvForecasted: "預報值",

  stationPrefix: "測站 ",

  weatherDataUnavailable: "天氣資料不足",
  tempHigh: (val: number | string) => `高溫 ${val} 度`,
  tempLow: (val: number | string) => `低溫 ${val} 度`,
  precipPop: (val: number | string) => `降雨 ${val}%`,
  aqiLabel: (val: number | string) => `空氣品質 ${val}`,

  adjustedNotice: (reqDate: string, targetDate: string) =>
    `${reqDate} 的預報已結束，已顯示最早可用的 ${targetDate} 預報。`,
  warningBannerAriaLabel: "天氣特報",
  moreWarnings: (count: number) => `另有 ${count} 則特報`,

  dayStripAriaLabel: "七天預報選擇列",
  weeklyForecastTitle: "本週預報（共 7 天）",
  weeklyForecastHint: "點選任一天，即可查看該日的行前建議與日出日落",
  dateChangeFailed: (msg: string) => `日期切換失敗：${msg}`,

  highPrefix: "高 ",
  lowPrefix: "低 ",
  rainPrefix: "降雨 ",

  badgeAdvice: "行前建議",
  badgeMock: "示範資料",

  kickerSun: "日出日落",
  kickerMoon: "月出月沒",

  uvIndexLabel: (val: number | string) => `指數 ${val}`,
  aqiIndexLabel: (val: number | string) => `AQI ${val}`,
  gaugeDataUnavailable: "資料不足",

  favManageAriaLabel: "常用地點管理",
  favDefaultTag: "（預設）",
  favMoveUpAria: (name: string) => `向前移動 ${name}`,
  favMoveDownAria: (name: string) => `向後移動 ${name}`,
  favUnsetDefaultAria: (name: string) => `取消 ${name} 預設`,
  favSetDefaultAria: (name: string) => `設 ${name} 為預設`,
  favRemoveAria: (name: string) => `移除 ${name}`,
  favDone: "完成",
  favSectionAriaLabel: "常用地點",
  favEmpty: "尚無常用地點",
  favAddCurrentAria: "加入目前地點至常用",
  favAddCurrentBtn: "+ 加入目前地點",
  favEditBtn: "編輯",

  celestialArcAriaLabel: (label: string) => `${label}升落弧線`,
  moonPhaseDefault: "月相",

  formatDate: (month: number, date: number, weekday: string) => `${month}/${date}（${weekday}）`,
  formatWeekday: (weekday: string) => `週${weekday}`,
  weekdaysShort: ["日", "一", "二", "三", "四", "五", "六"],
};
