import { useState } from "react";
import type { Town } from "../lib/api";
import { MAX_FAVORITES } from "../lib/favoriteTowns";
import { useLocale } from "../lib/locale";
import { getTownFullLabel, getTownName } from "../lib/townLabel";

interface Props {
  towns: Town[];
  favorites: string[];
  defaultTown: string | null;
  currentTownCode: string;
  loading: boolean;
  onSelect: (town: Town) => void;
  onAdd: (code: string) => void;
  onRemove: (code: string) => void;
  onMoveForward: (code: string) => void;
  onMoveBack: (code: string) => void;
  onToggleDefault: (code: string) => void;
}

export default function FavoriteTowns({
  towns,
  favorites,
  defaultTown,
  currentTownCode,
  loading,
  onSelect,
  onAdd,
  onRemove,
  onMoveForward,
  onMoveBack,
  onToggleDefault,
}: Props) {
  const { locale, t } = useLocale();
  const [editing, setEditing] = useState(false);

  const canAdd =
    !favorites.includes(currentTownCode) && favorites.length < MAX_FAVORITES && !!currentTownCode;

  const resolveTown = (code: string): Town | undefined => towns.find((item) => item.code === code);

  if (editing) {
    return (
      <section className="fav-section" aria-label={t.favManageAriaLabel}>
        <ul className="fav-edit-list" role="list">
          {favorites.map((code, idx) => {
            const town = resolveTown(code);
            if (!town) return null;
            const isDefault = code === defaultTown;
            const label = getTownFullLabel(town, locale);
            const townName = getTownName(town, locale);
            return (
              <li key={code} className="fav-edit-item">
                <span className="fav-edit-item-name">
                  {label}
                  {isDefault && (
                    <span className="fav-default-star" aria-hidden="true">
                      ★
                    </span>
                  )}
                  {isDefault && <span className="sr-only">{t.favDefaultTag}</span>}
                </span>
                <div className="fav-edit-item-controls">
                  <button
                    type="button"
                    className="fav-ctrl-btn"
                    aria-label={t.favMoveUpAria(townName)}
                    disabled={idx === 0}
                    onClick={() => onMoveForward(code)}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="fav-ctrl-btn"
                    aria-label={t.favMoveDownAria(townName)}
                    disabled={idx === favorites.length - 1}
                    onClick={() => onMoveBack(code)}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className={`fav-ctrl-btn fav-ctrl-default${isDefault ? " fav-ctrl-default-active" : ""}`}
                    aria-pressed={isDefault}
                    aria-label={isDefault ? t.favUnsetDefaultAria(townName) : t.favSetDefaultAria(townName)}
                    onClick={() => onToggleDefault(code)}
                  >
                    ★
                  </button>
                  <button
                    type="button"
                    className="fav-ctrl-btn fav-ctrl-remove"
                    aria-label={t.favRemoveAria(townName)}
                    onClick={() => onRemove(code)}
                  >
                    ×
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          className="fav-done-btn"
          onClick={() => setEditing(false)}
        >
          {t.favDone}
        </button>
      </section>
    );
  }

  return (
    <section className="fav-section" aria-label={t.favSectionAriaLabel}>
      <div className="fav-bar">
        {favorites.length === 0 && (
          <span className="fav-empty">{t.favEmpty}</span>
        )}
        {favorites.map((code) => {
          const town = resolveTown(code);
          if (!town) return null;
          const isCurrent = code === currentTownCode;
          const isDefault = code === defaultTown;
          const fullLabel = getTownFullLabel(town, locale);
          return (
            <button
              key={code}
              type="button"
              className={`fav-chip${isCurrent ? " fav-chip-active" : ""}`}
              aria-pressed={isCurrent}
              aria-label={`${fullLabel}${isDefault ? t.favDefaultTag : ""}`}
              disabled={loading}
              onClick={() => onSelect(town)}
            >
              {fullLabel}
              {isDefault && (
                <span className="fav-default-star" aria-hidden="true">
                  ★
                </span>
              )}
            </button>
          );
        })}
        {canAdd && (
          <button
            type="button"
            className="fav-add-btn"
            aria-label={t.favAddCurrentAria}
            onClick={() => onAdd(currentTownCode)}
          >
            {t.favAddCurrentBtn}
          </button>
        )}
        {favorites.length > 0 && (
          <button
            type="button"
            className="fav-edit-btn"
            onClick={() => setEditing(true)}
          >
            {t.favEditBtn}
          </button>
        )}
      </div>
    </section>
  );
}
