"use client";
import type { ReactNode } from "react";
import { BaseButton } from "./BaseButton";
interface BaseModalProps { open: boolean; title: string; onClose: () => void; children: ReactNode }
export function BaseModal({ open, title, onClose, children }: BaseModalProps) { if (!open) return null; return <div className="fixed inset-0 z-10 grid place-items-center bg-black/40 p-4"><div className="w-full max-w-lg rounded bg-white p-6 shadow-xl"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">{title}</h2><BaseButton variant="secondary" onClick={onClose}>Close</BaseButton></div>{children}</div></div>; }
