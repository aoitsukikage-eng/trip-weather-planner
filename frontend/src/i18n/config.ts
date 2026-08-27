export const SUPPORTED_LOCALES = ["zh", "en", "ja"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "zh";

export function isSupportedLocale(locale: string | null | undefined): locale is Locale {
  return typeof locale === "string" && (SUPPORTED_LOCALES as readonly string[]).includes(locale);
}
