import { useState } from "react";
import type { Town } from "../lib/api";
import { MAX_FAVORITES } from "../lib/favoriteTowns";

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
  const [editing, setEditing] = useState(false);

  const canAdd =
    !favorites.includes(currentTownCode) && favorites.length < MAX_FAVORITES && !!currentTownCode;

  const resolveTown = (code: string): Town | undefined => towns.find((t) => t.code === code);

  if (editing) {
    return (
      <section className="fav-section" aria-label="常用地點管理">
        <ul className="fav-edit-list" role="list">
          {favorites.map((code, idx) => {
            const town = resolveTown(code);
            if (!town) return null;
            const isDefault = code === defaultTown;
            const label = `${town.city} ${town.name}`;
            return (
              <li key={code} className="fav-edit-item">
                <span className="fav-edit-item-name">
                  {label}
                  {isDefault && (
                    <span className="fav-default-star" aria-hidden="true">
                      ★
                    </span>
                  )}
                  {isDefault && <span className="sr-only">（預設）</span>}
                </span>
                <div className="fav-edit-item-controls">
                  <button
                    type="button"
                    className="fav-ctrl-btn"
                    aria-label={`向前移動 ${town.name}`}
                    disabled={idx === 0}
                    onClick={() => onMoveForward(code)}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="fav-ctrl-btn"
                    aria-label={`向後移動 ${town.name}`}
                    disabled={idx === favorites.length - 1}
                    onClick={() => onMoveBack(code)}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className={`fav-ctrl-btn fav-ctrl-default${isDefault ? " fav-ctrl-default-active" : ""}`}
                    aria-pressed={isDefault}
                    aria-label={isDefault ? `取消 ${town.name} 預設` : `設 ${town.name} 為預設`}
                    onClick={() => onToggleDefault(code)}
                  >
                    ★
                  </button>
                  <button
                    type="button"
                    className="fav-ctrl-btn fav-ctrl-remove"
                    aria-label={`移除 ${town.name}`}
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
          完成
        </button>
      </section>
    );
  }

  return (
    <section className="fav-section" aria-label="常用地點">
      <div className="fav-bar">
        {favorites.length === 0 && (
          <span className="fav-empty">尚無常用地點</span>
        )}
        {favorites.map((code) => {
          const town = resolveTown(code);
          if (!town) return null;
          const isCurrent = code === currentTownCode;
          const isDefault = code === defaultTown;
          return (
            <button
              key={code}
              type="button"
              className={`fav-chip${isCurrent ? " fav-chip-active" : ""}`}
              aria-pressed={isCurrent}
              aria-label={`${town.city} ${town.name}${isDefault ? "（預設）" : ""}`}
              disabled={loading}
              onClick={() => onSelect(town)}
            >
              {town.city} {town.name}
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
            aria-label="加入目前地點至常用"
            onClick={() => onAdd(currentTownCode)}
          >
            + 加入目前地點
          </button>
        )}
        {favorites.length > 0 && (
          <button
            type="button"
            className="fav-edit-btn"
            onClick={() => setEditing(true)}
          >
            編輯
          </button>
        )}
      </div>
    </section>
  );
}
