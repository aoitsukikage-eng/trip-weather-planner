import type { Dictionary } from "./types";

export const ja: Dictionary = {
  switchLangAriaLabel: "言語切り替え",

  appTitle: "旅行お天気プランナー",
  appTagline: "目的地を選択すると、週間天気、72時間推移、旅行前のアドバイスを確認できます。",
  loadingTowns: "市町村リストを読み込み中…",
  queryFailed: "取得失敗",
  queryFailedDefault: "取得に失敗しました。しばらく時間をおいてから再試行してください。",
  footerNote: "出発前に天候や日の出・日の入り情報を確認して、余裕のある旅行計画を。",

  labelCity: "県 / 市",
  labelTown: "市町村・区",
  btnQuerying: "検索中…",
  btnQuery: "天気を検索",

  hourlyChartTitle: "72時間（3時間ごと）の予報",
  hourlyChartSubtitle: "折れ線は気温と体感温度、\n下の青い棒は降水確率を示します。",
  legendTemp: "気温",
  legendApparentTemp: "体感温度",
  hourlyChartAriaLabel: "72時間（3時間ごと）の気温・降水確率グラフ",
  hourlyChartNote: "体感温度のデータが不足している場合、紫の曲線は表示されませんが、他の情報には影響しません。",

  sunAstroRef: (date: string) => `${date} の天文データを参照`,
  uvObserved: "観測値",
  uvForecasted: "予報値",

  stationPrefix: "観測所 ",

  weatherDataUnavailable: "気象データが不足しています",
  tempHigh: (val: number | string) => `最高気温 ${val}℃`,
  tempLow: (val: number | string) => `最低気温 ${val}℃`,
  precipPop: (val: number | string) => `降水確率 ${val}%`,
  aqiLabel: (val: number | string) => `空気質 (AQI) ${val}`,

  adjustedNotice: (reqDate: string, targetDate: string) =>
    `${reqDate} の予報期間は終了しました。利用可能な最古の ${targetDate} の予報を表示しています。`,
  warningBannerAriaLabel: "気象警報・注意報",
  moreWarnings: (count: number) => `他 ${count} 件の警報・注意報`,

  dayStripAriaLabel: "7日間予報選択バー",
  weeklyForecastTitle: "週間予報（7日間）",
  weeklyForecastHint: "日付を選択すると、その日のアドバイスと日の出・日の入りを確認できます",
  dateChangeFailed: (msg: string) => `日付の切り替えに失敗しました：${msg}`,

  highPrefix: "最高 ",
  lowPrefix: "最低 ",
  rainPrefix: "降水 ",

  badgeAdvice: "旅行アドバイス",
  badgeMock: "デモデータ",

  kickerSun: "日の出・日の入り",
  kickerMoon: "月の出・月の入り",

  uvIndexLabel: (val: number | string) => `インデックス ${val}`,
  aqiIndexLabel: (val: number | string) => `AQI ${val}`,
  gaugeDataUnavailable: "データ不足",

  favManageAriaLabel: "お気に入り管理",
  favDefaultTag: "（デフォルト）",
  favMoveUpAria: (name: string) => `${name} を上に移動`,
  favMoveDownAria: (name: string) => `${name} 下に移動`,
  favUnsetDefaultAria: (name: string) => `${name} のデフォルト設定を解除`,
  favSetDefaultAria: (name: string) => `${name} をデフォルトに設定`,
  favRemoveAria: (name: string) => `${name} を削除`,
  favDone: "完了",
  favSectionAriaLabel: "お気に入り",
  favEmpty: "お気に入りが登録されていません",
  favAddCurrentAria: "現在の場所をお気に入りに追加",
  favAddCurrentBtn: "+ 現在の場所を追加",
  favEditBtn: "編集",

  celestialArcAriaLabel: (label: string) => `${label}出没軌跡`,
  moonPhaseDefault: "月相",

  formatDate: (month: number, date: number, weekday: string) => `${month}/${date}（${weekday}）`,
  formatWeekday: (weekday: string) => `${weekday}曜日`,
  weekdaysShort: ["日", "月", "火", "水", "木", "金", "土"],
};
