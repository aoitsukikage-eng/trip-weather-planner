export const SUPPORTED_LOCALES = ["zh", "en", "ja"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "zh";

export const LOCALE_NAMES: Record<Locale, string> = {
  zh: "中文",
  en: "English",
  ja: "日本語",
};

export function isSupportedLocale(locale: string | null | undefined): locale is Locale {
  return typeof locale === "string" && (SUPPORTED_LOCALES as readonly string[]).includes(locale);
}
