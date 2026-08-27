import { createContext, useContext, useState, type ReactNode } from "react";
import {
  DEFAULT_LOCALE,
  getDictionary,
  isSupportedLocale,
  type Dictionary,
  type Locale,
} from "../i18n";

const STORAGE_KEY = "twp:locale";

export interface LocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Dictionary;
}

function resolveInitialLocale(): Locale {
  if (typeof window !== "undefined") {
    const searchParams = new URLSearchParams(window.location.search);
    const queryLang = searchParams.get("lang");
    if (isSupportedLocale(queryLang)) {
      return queryLang;
    }
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (isSupportedLocale(stored)) {
        return stored;
      }
    } catch {
      // ignore storage access errors
    }
  }
  return DEFAULT_LOCALE;
}

const defaultContextValue: LocaleContextType = {
  locale: DEFAULT_LOCALE,
  setLocale: () => {},
  t: getDictionary(DEFAULT_LOCALE),
};

export const LocaleContext = createContext<LocaleContextType>(defaultContextValue);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(resolveInitialLocale);

  const setLocale = (newLocale: Locale) => {
    if (!isSupportedLocale(newLocale)) return;
    setLocaleState(newLocale);
    try {
      localStorage.setItem(STORAGE_KEY, newLocale);
    } catch {
      // ignore storage access errors
    }
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("lang", newLocale);
      window.history.replaceState(null, "", url.toString());
    }
  };

  const t = getDictionary(locale);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextType {
  return useContext(LocaleContext) ?? defaultContextValue;
}
