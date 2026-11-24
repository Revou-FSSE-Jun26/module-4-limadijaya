"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "@/lib/cx";

export type BaseButtonVariant = "primary" | "secondary" | "destructive";

export interface BaseButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  variant?: BaseButtonVariant;
  loading?: boolean;
  /** Renders a link that looks like the button, for navigation actions. */
  href?: string;
  fullWidth?: boolean;
  children: ReactNode;
}

const VARIANTS: Record<BaseButtonVariant, string> = {
  primary: "bg-indigo-600 text-white hover:bg-indigo-700 focus-visible:outline-indigo-600",
  secondary: "bg-white text-slate-800 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus-visible:outline-slate-500",
  destructive: "bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600",
};

/** The only component that renders a button element (FE-11). */
export default function BaseButton({
  variant = "primary",
  loading = false,
  href,
  fullWidth = false,
  disabled,
  type = "button",
  children,
  ...rest
}: BaseButtonProps) {
  const classes = cx(
    "inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
    "focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
    VARIANTS[variant],
    fullWidth && "w-full",
  );
  if (href && !disabled) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }
  return (
    <button type={type} className={classes} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {loading ? <span aria-hidden="true" className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" /> : null}
      {children}
    </button>
  );
}