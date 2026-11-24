import type { ReactNode } from "react";
import { cx } from "@/lib/cx";

export type BaseBadgeColor = "gray" | "blue" | "green" | "red" | "yellow";

export interface BaseBadgeProps {
  color?: BaseBadgeColor;
  children: ReactNode;
}

const COLORS: Record<BaseBadgeColor, string> = {
  gray: "bg-slate-100 text-slate-700",
  blue: "bg-blue-100 text-blue-800",
  green: "bg-green-100 text-green-800",
  red: "bg-red-100 text-red-800",
  yellow: "bg-yellow-100 text-yellow-800",
};

/** Small label for roles, Done state, and counts. Text always carries the meaning, never color alone. */
export default function BaseBadge({ color = "gray", children }: BaseBadgeProps) {
  return (
    <span className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", COLORS[color])}>
      {children}
    </span>
  );
}