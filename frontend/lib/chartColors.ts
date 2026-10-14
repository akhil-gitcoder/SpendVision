// Validated categorical palette (see dataviz skill / references/palette.md).
// Order is fixed and must not be cycled independently per chart - colors are
// assigned to categories in a stable order so the same category always gets
// the same color across charts.
export const CATEGORICAL_COLORS = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
];

export const STATUS_COLORS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const CHART_INK = {
  primary: "#0b0b0b",
  secondary: "#52514e",
  muted: "#898781",
  grid: "#e1e0d9",
  baseline: "#c3c2b7",
};

const MAX_CATEGORICAL_SLOTS = 8;

/** Assigns a stable color to each category name, in the order given.
 * Anything past the validated 8-slot limit folds visually into the last
 * slot's neighbor rather than generating a new (unvalidated) hue. */
export function colorForIndex(index: number): string {
  return CATEGORICAL_COLORS[Math.min(index, MAX_CATEGORICAL_SLOTS - 1)];
}

/** Caps a sorted (descending) list of {category, amount} items to the
 * validated palette size, folding the remainder into an "Other" bucket. */
export function capToOtherBucket<T extends { category: string; amount: number }>(
  items: T[],
  maxSlots: number = MAX_CATEGORICAL_SLOTS
): { category: string; amount: number }[] {
  if (items.length <= maxSlots) return items;
  const head = items.slice(0, maxSlots - 1);
  const rest = items.slice(maxSlots - 1);
  const otherTotal = rest.reduce((sum, item) => sum + item.amount, 0);
  return [...head, { category: "Other", amount: otherTotal }];
}
