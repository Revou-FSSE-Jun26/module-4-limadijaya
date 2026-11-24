/* eslint-disable no-restricted-syntax -- this is the single approved button primitive. */
import type { ButtonHTMLAttributes, ReactNode } from "react";
interface BaseButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { variant?: "primary" | "secondary" | "destructive"; children: ReactNode }
export function BaseButton({ variant = "primary", children, className = "", ...props }: BaseButtonProps) { return <button className={`rounded px-4 py-2 font-medium ${variant === "primary" ? "bg-blue-600 text-white" : variant === "destructive" ? "bg-red-600 text-white" : "border bg-white"} ${className}`} {...props}>{children}</button>; }
