import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, test, vi } from "vitest";
import FavoriteTowns from "./FavoriteTowns";
import type { Town } from "../lib/api";

const TOWNS: Town[] = [
  { code: "taipei-xinyi", name: "信義區", city: "臺北市", lat: 25.03, lon: 121.57 },
  { code: "taipei-daan", name: "大安區", city: "臺北市", lat: 25.03, lon: 121.54 },
  { code: "hualien-hualien", name: "花蓮市", city: "花蓮縣", lat: 23.98, lon: 121.6 },
];

const defaultProps = {
  towns: TOWNS,
  favorites: [],
  defaultTown: null,
  currentTownCode: "taipei-xinyi",
  loading: false,
  onSelect: vi.fn(),
  onAdd: vi.fn(),
  onRemove: vi.fn(),
  onMoveForward: vi.fn(),
  onMoveBack: vi.fn(),
  onToggleDefault: vi.fn(),
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("FavoriteTowns — normal mode", () => {
  test("shows empty state when favorites list is empty", () => {
    render(<FavoriteTowns {...defaultProps} favorites={[]} />);
    expect(screen.getByText("尚無常用地點")).not.toBeNull();
  });

  test("renders a chip for each favorite", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
      />,
    );
    expect(screen.getByRole("button", { name: /信義區/ })).not.toBeNull();
    expect(screen.getByRole("button", { name: /花蓮市/ })).not.toBeNull();
  });

  test("chip for the current town has aria-pressed=true", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        currentTownCode="taipei-xinyi"
      />,
    );
    const xinyiBtn = screen.getByRole("button", { name: /信義區/ });
    expect(xinyiBtn.getAttribute("aria-pressed")).toBe("true");
    const hualienBtn = screen.getByRole("button", { name: /花蓮市/ });
    expect(hualienBtn.getAttribute("aria-pressed")).toBe("false");
  });

  test("clicking a chip calls onSelect with the correct town", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        onSelect={onSelect}
      />,
    );
    await user.click(screen.getByRole("button", { name: /花蓮市/ }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0]?.[0]).toMatchObject({ code: "hualien-hualien" });
  });

  test("chips are disabled while loading", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi"]}
        loading={true}
      />,
    );
    expect((screen.getByRole("button", { name: /信義區/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  test("default town chip shows star indicator", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi"]}
        defaultTown="taipei-xinyi"
      />,
    );
    // aria-label includes （預設）
    expect(screen.getByRole("button", { name: /信義區/ }).getAttribute("aria-label")).toContain("（預設）");
    // visible star present
    expect(screen.getByText("★")).not.toBeNull();
  });

  test("shows 加入目前地點 when current town is not in favorites and limit not reached", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["hualien-hualien"]}
        currentTownCode="taipei-xinyi"
      />,
    );
    expect(screen.getByRole("button", { name: /加入目前地點/ })).not.toBeNull();
  });

  test("hides 加入目前地點 when current town is already a favorite", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi"]}
        currentTownCode="taipei-xinyi"
      />,
    );
    expect(screen.queryByRole("button", { name: /加入目前地點/ })).toBeNull();
  });

  test("hides 加入目前地點 when favorites are at MAX (6)", () => {
    const full = TOWNS.map((t) => t.code).concat(
      ["a", "b", "c"].map((s) => `extra-${s}`),
    ).slice(0, 6);
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={full}
        currentTownCode="taipei-daan"
      />,
    );
    expect(screen.queryByRole("button", { name: /加入目前地點/ })).toBeNull();
  });

  test("clicking 加入目前地點 calls onAdd with the currentTownCode", async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={[]}
        currentTownCode="taipei-xinyi"
        onAdd={onAdd}
      />,
    );
    await user.click(screen.getByRole("button", { name: /加入目前地點/ }));
    expect(onAdd).toHaveBeenCalledWith("taipei-xinyi");
  });

  test("shows 編輯 button only when favorites list is non-empty", () => {
    const { rerender } = render(<FavoriteTowns {...defaultProps} favorites={[]} />);
    expect(screen.queryByRole("button", { name: "編輯" })).toBeNull();

    rerender(<FavoriteTowns {...defaultProps} favorites={["taipei-xinyi"]} />);
    expect(screen.getByRole("button", { name: "編輯" })).not.toBeNull();
  });
});

describe("FavoriteTowns — edit mode", () => {
  test("clicking 編輯 enters edit mode and shows 完成", async () => {
    const user = userEvent.setup();
    render(<FavoriteTowns {...defaultProps} favorites={["taipei-xinyi"]} />);
    await user.click(screen.getByRole("button", { name: "編輯" }));
    expect(screen.getByRole("button", { name: "完成" })).not.toBeNull();
  });

  test("clicking 完成 exits edit mode", async () => {
    const user = userEvent.setup();
    render(<FavoriteTowns {...defaultProps} favorites={["taipei-xinyi"]} />);
    await user.click(screen.getByRole("button", { name: "編輯" }));
    await user.click(screen.getByRole("button", { name: "完成" }));
    expect(screen.queryByRole("button", { name: "完成" })).toBeNull();
  });

  test("remove button calls onRemove with the correct code", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        onRemove={onRemove}
      />,
    );
    await user.click(screen.getByRole("button", { name: "編輯" }));
    await user.click(screen.getByRole("button", { name: "移除 花蓮市" }));
    expect(onRemove).toHaveBeenCalledWith("hualien-hualien");
  });

  test("move forward button calls onMoveForward and is disabled for first item", async () => {
    const user = userEvent.setup();
    const onMoveForward = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        onMoveForward={onMoveForward}
      />,
    );
    await user.click(screen.getByRole("button", { name: "編輯" }));
    const firstForward = screen.getByRole("button", { name: "向前移動 信義區" });
    expect((firstForward as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "向前移動 花蓮市" }));
    expect(onMoveForward).toHaveBeenCalledWith("hualien-hualien");
  });

  test("move back button calls onMoveBack and is disabled for last item", async () => {
    const user = userEvent.setup();
    const onMoveBack = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        onMoveBack={onMoveBack}
      />,
    );
    await user.click(screen.getByRole("button", { name: "編輯" }));
    const lastBack = screen.getByRole("button", { name: "向後移動 花蓮市" });
    expect((lastBack as HTMLButtonElement).disabled).toBe(true);
    await user.click(screen.getByRole("button", { name: "向後移動 信義區" }));
    expect(onMoveBack).toHaveBeenCalledWith("taipei-xinyi");
  });

  test("set-default button calls onToggleDefault and shows aria-pressed", async () => {
    const user = userEvent.setup();
    const onToggleDefault = vi.fn();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "hualien-hualien"]}
        defaultTown={null}
        onToggleDefault={onToggleDefault}
      />,
    );
    await user.click(screen.getByRole("button", { name: "編輯" }));
    const setDefaultBtn = screen.getByRole("button", { name: "設 信義區 為預設" });
    expect(setDefaultBtn.getAttribute("aria-pressed")).toBe("false");
    await user.click(setDefaultBtn);
    expect(onToggleDefault).toHaveBeenCalledWith("taipei-xinyi");
  });

  test("clear-default button shows correct label when town is already default", async () => {
    const user = userEvent.setup();
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi"]}
        defaultTown="taipei-xinyi"
      />,
    );
    await user.click(screen.getByRole("button", { name: "編輯" }));
    const btn = screen.getByRole("button", { name: "取消 信義區 預設" });
    expect(btn.getAttribute("aria-pressed")).toBe("true");
  });

  test("invalid favorite codes (town not in towns list) are silently skipped", () => {
    render(
      <FavoriteTowns
        {...defaultProps}
        favorites={["taipei-xinyi", "unknown-code"]}
      />,
    );
    expect(screen.getByRole("button", { name: /信義區/ })).not.toBeNull();
    expect(screen.queryByText("unknown-code")).toBeNull();
  });
});
