// Pure ordering helpers for the FLOAT order strategy (FE-15, design 7.9). No React imports.

export const SPACING = 1024;

/**
 * Order for a card placed between two neighbours.
 * - empty column: 1024
 * - before the first card: half of it when that stays positive and distinct, otherwise the same value (the server then rebalances)
 * - after the last card: previous + 1024
 * - between: the midpoint when strictly between, otherwise the next value (a tie the server rebalances)
 */
export function computeCardOrder(prev: number | null, next: number | null): number {
  if (prev === null && next === null) return SPACING;
  if (prev === null && next !== null) {
    const half = next / 2;
    return half > 0 && half < next ? half : next;
  }
  if (prev !== null && next === null) return prev + SPACING;
  const lower = prev as number;
  const upper = next as number;
  const mid = lower + (upper - lower) / 2;
  return mid > lower && mid < upper ? mid : upper;
}

/**
 * Order for a column placed between two neighbours, or null when no distinct value exists.
 * The caller then normalizes every column.
 */
export function computeColumnOrder(prev: number | null, next: number | null): number | null {
  if (prev === null && next === null) return SPACING;
  if (prev === null && next !== null) {
    const half = next / 2;
    return half > 0 && half < next ? half : null;
  }
  if (prev !== null && next === null) return prev + SPACING;
  const lower = prev as number;
  const upper = next as number;
  const mid = lower + (upper - lower) / 2;
  return mid > lower && mid < upper ? mid : null;
}

export interface OrderedColumn {
  id: string;
}

/** Every loaded column once, numbered 1024, 2048, ... in the intended final sequence. */
export function normalizeColumns(
  columns: OrderedColumn[],
  movedId: string,
  index: number,
): { id: string; order: number }[] {
  const without = columns.filter((column) => column.id !== movedId);
  const moved = columns.find((column) => column.id === movedId);
  if (!moved) return without.map((column, i) => ({ id: column.id, order: SPACING * (i + 1) }));
  const clamped = Math.max(0, Math.min(index, without.length));
  const sequence = [...without.slice(0, clamped), moved, ...without.slice(clamped)];
  return sequence.map((column, i) => ({ id: column.id, order: SPACING * (i + 1) }));
}
