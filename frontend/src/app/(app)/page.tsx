import BoardCard from "@/components/boards/BoardCard";
import CreateBoardForm from "@/components/boards/CreateBoardForm";
import ErrorState from "@/components/boards/ErrorState";
import { serverGetResult } from "@/lib/serverApi.server";
import type { BoardSummary } from "@/types/api";

/** Dashboard: Server Component that lists the user's boards (FRONT-005). */
export default async function DashboardPage() {
  const result = await serverGetResult<BoardSummary[]>("/api/boards");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Your boards</h1>
      {result.error !== null ? (
        <ErrorState message={result.error} />
      ) : result.data.length === 0 ? (
        <p className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-600">
          You have no boards yet. Create your first one below.
        </p>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {result.data.map((board) => (
            <li key={board.id}>
              <BoardCard board={board} />
            </li>
          ))}
        </ul>
      )}
      <section aria-labelledby="create-board" className="max-w-md rounded-lg border border-slate-200 bg-white p-4">
        <h2 id="create-board" className="mb-3 text-base font-semibold">
          Create a board
        </h2>
        <CreateBoardForm />
      </section>
    </div>
  );
}