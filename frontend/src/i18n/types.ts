export type Dictionary = {
  switchLangLabel: string;
  switchLangAriaLabel: string;
  localeNames: Record<string, string>;

  // App.tsx
  appTitle: string;
  appTagline: string;
  loadingTowns: string;
  queryFailed: string;
  queryFailedDefault: string;
  footerNote: string;

  // TripForm.tsx
  labelCity: string;
  labelTown: string;
  btnQuerying: string;
  btnQuery: string;

  // ForecastView.tsx
  hourlyChartTitle: string;
  hourlyChartSubtitle: string;
  legendTemp: string;
  legendApparentTemp: string;
  hourlyChartAriaLabel: string;
  hourlyChartNote: string;

  sunAstroRef: (date: string) => string;
  uvObserved: string;
  uvForecasted: string;

  stationPrefix: string;

  weatherDataUnavailable: string;
  tempHigh: (val: number | string) => string;
  tempLow: (val: number | string) => string;
  precipPop: (val: number | string) => string;
  aqiLabel: (val: number | string) => string;

  adjustedNotice: (reqDate: string, targetDate: string) => string;
  warningBannerAriaLabel: string;
  moreWarnings: (count: number) => string;

  dayStripAriaLabel: string;
  weeklyForecastTitle: string;
  weeklyForecastHint: string;
  dateChangeFailed: (msg: string) => string;

  highPrefix: string;
  lowPrefix: string;
  rainPrefix: string;

  badgeAdvice: string;
  badgeMock: string;

  kickerSun: string;
  kickerMoon: string;

  // StatusGauge.tsx
  uvIndexLabel: (val: number | string) => string;
  aqiIndexLabel: (val: number | string) => string;
  gaugeDataUnavailable: string;

  // FavoriteTowns.tsx
  favManageAriaLabel: string;
  favDefaultTag: string;
  favMoveUpAria: (name: string) => string;
  favMoveDownAria: (name: string) => string;
  favUnsetDefaultAria: (name: string) => string;
  favSetDefaultAria: (name: string) => string;
  favRemoveAria: (name: string) => string;
  favDone: string;
  favSectionAriaLabel: string;
  favEmpty: string;
  favAddCurrentAria: string;
  favAddCurrentBtn: string;
  favEditBtn: string;

  // CelestialArc.tsx
  celestialArcAriaLabel: (label: string) => string;
  moonPhaseDefault: string;

  // Date formatting helpers
  formatDate: (month: number, date: number, weekday: string) => string;
  formatWeekday: (weekday: string) => string;
  weekdaysShort: readonly string[];
};
