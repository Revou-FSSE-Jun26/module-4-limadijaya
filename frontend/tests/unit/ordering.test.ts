import { describe, expect, it } from "vitest";
import { computeCardOrder, computeColumnOrder, normalizeColumns } from "@/lib/ordering";

describe("computeCardOrder", () => {
  it("returns 1024 for an empty column", () => expect(computeCardOrder(null, null)).toBe(1024));
  it("halves the first order when placed before the first card", () => expect(computeCardOrder(null, 1024)).toBe(512));
  it("adds 1024 after the last card", () => expect(computeCardOrder(2048, null)).toBe(3072));
  it("uses the midpoint between two cards", () => expect(computeCardOrder(1024, 2048)).toBe(1536));
  it("falls back to the next value when no distinct midpoint exists (the server rebalances)", () => {
    const next = 1 + Number.EPSILON;
    expect(computeCardOrder(1, next)).toBe(next);
  });
  it("always returns a positive finite number", () => {
    let order = 1024;
    for (let i = 0; i < 40; i += 1) order = computeCardOrder(null, order);
    expect(order).toBeGreaterThan(0);
    expect(Number.isFinite(order)).toBe(true);
  });
});

describe("computeColumnOrder", () => {
  it("returns the midpoint", () => expect(computeColumnOrder(1024, 2048)).toBe(1536));
  it("returns null when no distinct value exists", () => {
    expect(computeColumnOrder(1, 1 + Number.EPSILON)).toBeNull();
  });
  it("handles the ends", () => {
    expect(computeColumnOrder(null, null)).toBe(1024);
    expect(computeColumnOrder(2048, null)).toBe(3072);
    expect(computeColumnOrder(null, 1024)).toBe(512);
  });
});

describe("normalizeColumns", () => {
  it("numbers every column once in the intended sequence", () => {
    const columns = [{ id: "a" }, { id: "b" }, { id: "c" }];
    expect(normalizeColumns(columns, "c", 0)).toEqual([
      { id: "c", order: 1024 },
      { id: "a", order: 2048 },
      { id: "b", order: 3072 },
    ]);
  });
  it("clamps the index", () => {
    const result = normalizeColumns([{ id: "a" }, { id: "b" }], "a", 99);
    expect(result.map((entry) => entry.id)).toEqual(["b", "a"]);
  });
});