import { DEFAULT_LOCALE, type Locale } from "./config";
import { en } from "./en";
import type { Dictionary } from "./types";
import { zh } from "./zh";

export * from "./config";
export * from "./types";

export const DICTIONARIES: Record<Locale, Dictionary> = {
  zh,
  en,
};

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES[DEFAULT_LOCALE];
}
