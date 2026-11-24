import BoardView from "@/components/boards/BoardView";
import ErrorState from "@/components/boards/ErrorState";
import { serverGet, serverGetResult } from "@/lib/serverApi.server";
import type { Analytics, BoardDetail } from "@/types/api";

export interface BoardPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ card?: string }>;
}

/** Board detail: Server Component that loads the board and its analytics, then renders the Kanban view. */
export default async function BoardPage({ params, searchParams }: BoardPageProps) {
  const { id } = await params;
  const { card } = await searchParams;
  let board: BoardDetail;
  try {
    board = await serverGet<BoardDetail>(`/api/boards/${id}`);
  } catch (error) {
    if (error instanceof Error && "digest" in error) throw error; // redirect() and notFound() signals
    return <ErrorState message={error instanceof Error ? error.message : "The board could not be loaded."} />;
  }
  const analytics = await serverGetResult<Analytics>(`/api/boards/${id}/analytics`);
  return (
    <BoardView
      initialBoard={board}
      initialAnalytics={analytics.data}
      analyticsError={analytics.error}
      initialCardId={card ?? null}
    />
  );
}