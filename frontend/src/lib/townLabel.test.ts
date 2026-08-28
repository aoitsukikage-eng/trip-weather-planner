import { describe, expect, test } from "vitest";
import { getCityName, getTownFullLabel, getTownName } from "./townLabel";

describe("townLabel helpers", () => {
  const townWithEn = {
    code: "taipei-xinyi",
    name: "信義區",
    city: "臺北市",
    name_en: "Xinyi District",
    city_en: "Taipei City",
  };

  const townWithoutEn = {
    code: "cwa-1000201",
    name: "卓溪鄉",
    city: "花蓮縣",
    name_en: null,
    city_en: "Hualien County",
  };

  const townWithEmptyEn = {
    code: "cwa-1000202",
    name: "萬榮鄉",
    city: "花蓮縣",
    name_en: "",
    city_en: null,
  };

  test("getTownName returns English name when present for en locale, falls back to Chinese name when null/empty or zh locale", () => {
    expect(getTownName(townWithEn, "en")).toBe("Xinyi District");
    expect(getTownName(townWithEn, "zh")).toBe("信義區");

    expect(getTownName(townWithoutEn, "en")).toBe("卓溪鄉");
    expect(getTownName(townWithEmptyEn, "en")).toBe("萬榮鄉");
  });

  test("getCityName returns English city when present for en locale, falls back to Chinese city when null/empty or zh locale", () => {
    expect(getCityName(townWithEn, "en")).toBe("Taipei City");
    expect(getCityName(townWithEn, "zh")).toBe("臺北市");

    expect(getCityName(townWithoutEn, "en")).toBe("Hualien County");
    expect(getCityName(townWithEmptyEn, "en")).toBe("花蓮縣");
  });

  test("getTownFullLabel combines localized city and town names", () => {
    expect(getTownFullLabel(townWithEn, "en")).toBe("Taipei City Xinyi District");
    expect(getTownFullLabel(townWithEn, "zh")).toBe("臺北市 信義區");
    expect(getTownFullLabel(townWithoutEn, "en")).toBe("Hualien County 卓溪鄉");
  });

  test("getTownName and getCityName return Traditional Chinese name/city for ja locale (AC4 passthrough)", () => {
    expect(getTownName(townWithEn, "ja")).toBe("信義區");
    expect(getCityName(townWithEn, "ja")).toBe("臺北市");
    expect(getTownFullLabel(townWithEn, "ja")).toBe("臺北市 信義區");
  });
});
