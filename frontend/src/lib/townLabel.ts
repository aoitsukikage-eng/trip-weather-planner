import type { Town } from "./api";

export function getTownName(
  town: Pick<Town, "name"> & Partial<Pick<Town, "name_en">>,
  locale: string
): string {
  if (locale === "en" && town.name_en && town.name_en.trim()) {
    return town.name_en.trim();
  }
  return town.name;
}

export function getCityName(
  town: Pick<Town, "city"> & Partial<Pick<Town, "city_en">>,
  locale: string
): string {
  if (locale === "en" && town.city_en && town.city_en.trim()) {
    return town.city_en.trim();
  }
  return town.city;
}

export function getTownFullLabel(
  town: Pick<Town, "name" | "city"> & Partial<Pick<Town, "name_en" | "city_en">>,
  locale: string
): string {
  return `${getCityName(town, locale)} ${getTownName(town, locale)}`;
}
