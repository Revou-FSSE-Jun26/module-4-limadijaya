"use client";
import { useState } from "react";
import { apiClient } from "@/lib/apiClient";
export function useDragAndDrop<T extends { id: string }>(items: T[], update: (items: T[]) => void) {
  const [dragged, setDragged] = useState<T | null>(null);
  const onDragStart = (item: T) => setDragged(item);
  const onDrop = async (target: T) => { if (!dragged || dragged.id === target.id) return; const previous = items; const next = items.map(item => item.id === dragged.id ? target : item); update(next); try { await apiClient(`/cards/${dragged.id}/position`, { method: "PATCH", body: JSON.stringify({ column_id: target.id, order: 1024 }) }, localStorage.getItem("revotask-session") ? JSON.parse(localStorage.getItem("revotask-session")!).token : undefined); } catch { update(previous); } setDragged(null); };
  return { onDragStart, onDrop };
}
