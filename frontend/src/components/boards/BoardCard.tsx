import Link from "next/link";
import type { BoardSummary } from "@/types/api";

export interface BoardCardProps {
  board: BoardSummary;
}

/** A link tile for one board on the dashboard. No hooks and no handlers. */
export default function BoardCard({ board }: BoardCardProps) {
  return (
    <Link
      href={`/boards/${board.id}`}
      className="block rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-indigo-400 hover:shadow focus-visible:outline-2 focus-visible:outline-indigo-600"
    >
      <h3 className="truncate text-base font-semibold text-slate-900">{board.name}</h3>
      <p className="mt-1 text-xs text-slate-500">Created {board.created_at.slice(0, 10)}</p>
    </Link>
  );
}