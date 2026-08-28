import { DEFAULT_LOCALE, type Locale } from "./config";
import { en } from "./en";
import { ja } from "./ja";
import type { Dictionary } from "./types";
import { zh } from "./zh";

export * from "./config";
export * from "./types";

export const DICTIONARIES: Record<Locale, Dictionary> = {
  zh,
  en,
  ja,
};

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES[DEFAULT_LOCALE];
}
