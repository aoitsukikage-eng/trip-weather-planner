import type { Dictionary } from "./types";

export const en: Dictionary = {
  switchLangAriaLabel: "Switch language",

  appTitle: "Trip Weather Planner",
  appTagline: "Select a destination to view 7-day forecast, 72-hour trends, and pre-trip reminders.",
  loadingTowns: "Loading township list…",
  queryFailed: "Query Failed",
  queryFailedDefault: "Query failed, please try again later.",
  footerNote: "Check weather and daylight info before heading out for a smooth trip.",

  labelCity: "County / City",
  labelTown: "Township / District",
  btnQuerying: "Searching…",
  btnQuery: "Search Weather",

  hourlyChartTitle: "72-Hour Forecast (3-Hour Slots)",
  hourlyChartSubtitle: "Curves show temperature & apparent temp; bottom bars show precipitation probability.",
  legendTemp: "Temperature",
  legendApparentTemp: "Apparent Temp",
  hourlyChartAriaLabel: "72-hour temperature and precipitation probability chart",
  hourlyChartNote: "If apparent temperature data is unavailable, the purple curve is omitted without affecting other data.",

  sunAstroRef: (date: string) => `Ref: ${date} astronomical data`,
  uvObserved: "Observed",
  uvForecasted: "Forecasted",

  stationPrefix: "Station ",

  weatherDataUnavailable: "Weather data unavailable",
  tempHigh: (val: number | string) => `High ${val}°C`,
  tempLow: (val: number | string) => `Low ${val}°C`,
  precipPop: (val: number | string) => `Precip ${val}%`,
  aqiLabel: (val: number | string) => `AQI ${val}`,

  adjustedNotice: (reqDate: string, targetDate: string) =>
    `Forecast for ${reqDate} has ended. Showing the earliest available forecast for ${targetDate}.`,
  warningBannerAriaLabel: "Weather Warnings",
  moreWarnings: (count: number) => `${count} more warnings`,

  dayStripAriaLabel: "7-day forecast selector",
  weeklyForecastTitle: "Weekly Forecast (7 Days)",
  weeklyForecastHint: "Click any day to view pre-trip advice and sunrise/sunset",
  dateChangeFailed: (msg: string) => `Date change failed: ${msg}`,

  highPrefix: "High ",
  lowPrefix: "Low ",
  rainPrefix: "Rain ",

  badgeAdvice: "Pre-trip Advice",
  badgeMock: "Demo Data",

  kickerSun: "Sunrise & Sunset",
  kickerMoon: "Moonrise & Moonset",

  uvIndexLabel: (val: number | string) => `Index ${val}`,
  aqiIndexLabel: (val: number | string) => `AQI ${val}`,
  gaugeDataUnavailable: "Data unavailable",

  favManageAriaLabel: "Manage Favorite Places",
  favDefaultTag: " (Default)",
  favMoveUpAria: (name: string) => `Move ${name} up`,
  favMoveDownAria: (name: string) => `Move ${name} down`,
  favUnsetDefaultAria: (name: string) => `Unset ${name} as default`,
  favSetDefaultAria: (name: string) => `Set ${name} as default`,
  favRemoveAria: (name: string) => `Remove ${name}`,
  favDone: "Done",
  favSectionAriaLabel: "Favorite Places",
  favEmpty: "No favorite places",
  favAddCurrentAria: "Add current place to favorites",
  favAddCurrentBtn: "+ Add Current Place",
  favEditBtn: "Edit",

  celestialArcAriaLabel: (label: string) => `${label} rise/set arc`,
  moonPhaseDefault: "Moon Phase",

  formatDate: (month: number, date: number, weekday: string) => `${month}/${date} (${weekday})`,
  formatWeekday: (weekday: string) => weekday,
  weekdaysShort: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
};
