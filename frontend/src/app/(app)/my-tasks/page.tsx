import Link from "next/link";
import ErrorState from "@/components/boards/ErrorState";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import { serverGetResult } from "@/lib/serverApi.server";
import type { MyTaskCard } from "@/types/api";

/** My Tasks: cards assigned to the current user, grouped by board name (FRONT-009). */
export default async function MyTasksPage() {
  const result = await serverGetResult<MyTaskCard[]>("/api/cards?assignee=me");
  if (result.error !== null) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">My Tasks</h1>
        <ErrorState message={result.error} />
      </div>
    );
  }
  const groups = new Map<string, { boardId: string; cards: MyTaskCard[] }>();
  for (const card of result.data) {
    const group = groups.get(card.board_name) ?? { boardId: card.board_id, cards: [] };
    group.cards.push(card);
    groups.set(card.board_name, group);
  }
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">My Tasks</h1>
      {groups.size === 0 ? (
        <div className="space-y-3 rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-600">
          <p>No cards are assigned to you yet.</p>
          <BaseButton href="/">Go to your boards</BaseButton>
        </div>
      ) : (
        Array.from(groups.entries()).map(([boardName, group]) => (
          <section key={group.boardId} aria-labelledby={`board-${group.boardId}`}>
            <h2 id={`board-${group.boardId}`} className="mb-2 text-lg font-semibold">
              {boardName}
            </h2>
            <ul className="space-y-2">
              {group.cards.map((card) => (
                <li key={card.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-slate-200 bg-white p-3">
                  <Link href={`/boards/${card.board_id}?card=${card.id}`} className="font-medium text-indigo-700 underline">
                    {card.title}
                  </Link>
                  {card.completed_at ? <BaseBadge color="green">Done</BaseBadge> : <BaseBadge>Open</BaseBadge>}
                </li>
              ))}
            </ul>
            <div className="mt-2">
              <BaseButton variant="secondary" href={`/boards/${group.boardId}`}>
                Open board
              </BaseButton>
            </div>
          </section>
        ))
      )}
    </div>
  );
}