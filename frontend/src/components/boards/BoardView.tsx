"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AnalyticsPanel from "@/components/boards/AnalyticsPanel";
import CardDetailModal from "@/components/boards/CardDetailModal";
import CardItem from "@/components/boards/CardItem";
import CardMoveMenu from "@/components/boards/CardMoveMenu";
import CardSearchInput from "@/components/boards/CardSearchInput";
import ColumnHeader from "@/components/boards/ColumnHeader";
import ConfirmDialog from "@/components/boards/ConfirmDialog";
import TextForm from "@/components/boards/TextForm";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";
import { useDragAndDrop } from "@/hooks/useDragAndDrop";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { api } from "@/lib/apiClient";
import { cx } from "@/lib/cx";
import { toastSuccess } from "@/lib/toast";
import type { Analytics, BoardDetail, BoardSummary, Card, Column, ColumnWithCards, UserPublic } from "@/types/api";

export interface BoardViewProps {
  initialBoard: BoardDetail;
  initialAnalytics: Analytics | null;
  analyticsError: string | null;
  /** Card id from the ?card= deep link, or null. */
  initialCardId: string | null;
}

/** The Kanban board: columns, cards, search, drag-and-drop, card modal, and analytics (FRONT-006 to FRONT-026). */
export default function BoardView({ initialBoard, initialAnalytics, analyticsError, initialCardId }: BoardViewProps) {
  const router = useRouter();
  const handleError = useErrorHandler();
  const isAdministrator = initialBoard.role === "administrator";

  const boardRef = useRef(initialBoard);
  const [board, setBoard] = useState(initialBoard);
  const [analytics, setAnalytics] = useState(initialAnalytics);
  const [analyticsFailure, setAnalyticsFailure] = useState(analyticsError);
  const [term, setTerm] = useState("");
  const [openCardId, setOpenCardId] = useState<string | null>(initialCardId);
  const [movingCardId, setMovingCardId] = useState<string | null>(null);
  const [liveMessage, setLiveMessage] = useState("");
  const [renamingBoard, setRenamingBoard] = useState(false);
  const [deletingBoard, setDeletingBoard] = useState(false);
  const [addingMember, setAddingMember] = useState(false);

  const getBoard = useCallback(() => boardRef.current, []);
  const commitBoard = useCallback((next: BoardDetail) => {
    boardRef.current = next;
    setBoard(next);
  }, []);

  const refetchAnalytics = useCallback(async () => {
    try {
      setAnalytics(await api.get<Analytics>(`/api/boards/${boardRef.current.id}/analytics`));
      setAnalyticsFailure(null);
    } catch (error) {
      setAnalyticsFailure(error instanceof Error ? error.message : "Unknown error");
    }
  }, []);

  const refetchBoard = useCallback(async () => {
    try {
      commitBoard(await api.get<BoardDetail>(`/api/boards/${boardRef.current.id}`));
    } catch (error) {
      handleError(error);
    }
  }, [commitBoard, handleError]);

  const announce = useCallback((message: string) => setLiveMessage(message), []);

  const { draggingCardId, overColumnId, moveCardTo, moveColumnTo, cardDragProps, columnDropProps } = useDragAndDrop({
    getBoard,
    commitBoard,
    refetchBoard,
    announce,
    onMoved: () => void refetchAnalytics(),
  });

  // Keep the board in sync when the Server Component sends fresh data (for example after router.refresh()).
  useEffect(() => {
    boardRef.current = initialBoard;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setBoard(initialBoard);
  }, [initialBoard]);

  const normalizedTerm = term.trim().toLowerCase();
  const allCards = board.columns.flatMap((column) => column.cards);
  const openCard = allCards.find((card) => card.id === openCardId) ?? null;
  const movingCard = allCards.find((card) => card.id === movingCardId) ?? null;
  const memberName = (id: string | null) => board.members.find((member) => member.id === id)?.name ?? null;
  const visibleCount = normalizedTerm ? allCards.filter((card) => card.title.toLowerCase().includes(normalizedTerm)).length : allCards.length;

  const updateColumns = (update: (columns: ColumnWithCards[]) => ColumnWithCards[]) => {
    const current = boardRef.current;
    commitBoard({ ...current, columns: update(current.columns) });
  };

  async function addColumn(name: string) {
    const created = await api.post<Column>(`/api/boards/${board.id}/columns`, { name });
    updateColumns((columns) => [...columns, { ...created, cards: [] }]);
    void refetchAnalytics();
  }

  async function renameColumn(columnId: string, name: string) {
    const updated = await api.patch<Column>(`/api/columns/${columnId}`, { name });
    updateColumns((columns) => columns.map((column) => (column.id === columnId ? { ...column, ...updated } : column)));
  }

  async function toggleDone(columnId: string, isDone: boolean) {
    try {
      await api.patch<Column>(`/api/columns/${columnId}`, { is_done: isDone });
      await refetchBoard();
      void refetchAnalytics();
    } catch (error) {
      handleError(error);
    }
  }

  async function deleteColumn(columnId: string) {
    await api.delete(`/api/columns/${columnId}`);
    updateColumns((columns) => columns.filter((column) => column.id !== columnId));
    toastSuccess("Column deleted");
    void refetchAnalytics();
  }

  async function addCard(columnId: string, title: string) {
    const created = await api.post<Card>(`/api/columns/${columnId}/cards`, { title });
    updateColumns((columns) => columns.map((column) => (column.id === columnId ? { ...column, cards: [...column.cards, created] } : column)));
    void refetchAnalytics();
  }

  function replaceCard(updated: Card) {
    updateColumns((columns) =>
      columns.map((column) => ({ ...column, cards: column.cards.map((card) => (card.id === updated.id ? updated : card)) })),
    );
  }

  function removeCard(cardId: string) {
    updateColumns((columns) => columns.map((column) => ({ ...column, cards: column.cards.filter((card) => card.id !== cardId) })));
    setOpenCardId(null);
    void refetchAnalytics();
  }

  async function renameBoard(name: string) {
    const updated = await api.patch<BoardSummary>(`/api/boards/${board.id}`, { name });
    commitBoard({ ...boardRef.current, name: updated.name });
    setRenamingBoard(false);
    toastSuccess("Board renamed");
  }

  async function deleteBoard() {
    await api.delete(`/api/boards/${board.id}`);
    toastSuccess("Board deleted");
    router.push("/");
    router.refresh();
  }

  async function addMember(email: string) {
    const user = await api.post<UserPublic>(`/api/boards/${board.id}/members`, { email });
    commitBoard({
      ...boardRef.current,
      members: [...boardRef.current.members, { id: user.id, name: user.name }].sort((a, b) => a.name.localeCompare(b.name)),
    });
    setAddingMember(false);
    toastSuccess(`${user.name} was added to the board`);
  }

  const deepLinkMissing = initialCardId !== null && openCardId === initialCardId && !openCard;

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold text-slate-900">{board.name}</h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-600">
            <BaseBadge color={isAdministrator ? "yellow" : "gray"}>{board.role}</BaseBadge>
            <span>Members: {board.members.map((member) => member.name).join(", ")}</span>
          </p>
        </div>
        {isAdministrator ? (
          <div className="flex flex-wrap gap-2">
            <BaseButton variant="secondary" onClick={() => setAddingMember(true)}>
              Add member
            </BaseButton>
            <BaseButton variant="secondary" onClick={() => setRenamingBoard(true)}>
              Rename board
            </BaseButton>
            <BaseButton variant="destructive" onClick={() => setDeletingBoard(true)}>
              Delete board
            </BaseButton>
          </div>
        ) : null}
      </header>

      {deepLinkMissing ? (
        <p role="status" className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          This card is no longer available.{" "}
          <BaseButton variant="secondary" onClick={() => setOpenCardId(null)}>
            Dismiss
          </BaseButton>
        </p>
      ) : null}

      <div className="flex flex-wrap items-end justify-between gap-3">
        <CardSearchInput onTermChange={setTerm} />
        <div className="w-full sm:w-72">
          <TextForm label="New column name" submitLabel="Add column" placeholder="New column" onSubmit={addColumn} compact />
        </div>
      </div>
      {normalizedTerm && visibleCount === 0 ? (
        <p role="status" className="text-sm text-slate-600">
          No cards match your search.
        </p>
      ) : null}

      {board.columns.length === 0 ? (
        <p className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-600">
          This board has no columns yet. Add one above.
        </p>
      ) : (
        <div className="relative flex gap-4 overflow-x-auto pb-4" data-testid="columns-scroller">
          {board.columns.map((column, index) => (
            <section
              key={column.id}
              data-testid="column"
              data-column-id={column.id}
              aria-label={`Column ${column.name}`}
              className="w-72 shrink-0 rounded-lg bg-slate-100 p-3"
            >
              <ColumnHeader
                column={column}
                cardCount={column.cards.length}
                index={index}
                total={board.columns.length}
                isAdministrator={isAdministrator}
                onRename={(name) => renameColumn(column.id, name)}
                onToggleDone={(isDone) => toggleDone(column.id, isDone)}
                onDelete={() => deleteColumn(column.id)}
                onMove={(direction) => void moveColumnTo(column.id, index + direction)}
              />
              <ul
                data-testid="column-dropzone"
                aria-label={`Cards in ${column.name}`}
                {...columnDropProps(column.id)}
                className={cx(
                  "mt-3 min-h-20 space-y-2 rounded-md p-1",
                  overColumnId === column.id && "bg-indigo-100 ring-2 ring-indigo-400",
                )}
              >
                {column.cards.map((card) => (
                  <CardItem
                    key={card.id}
                    card={card}
                    assigneeName={memberName(card.assignee_id)}
                    dragging={draggingCardId === card.id}
                    hidden={Boolean(normalizedTerm) && !card.title.toLowerCase().includes(normalizedTerm)}
                    dragProps={cardDragProps(card.id)}
                    onOpen={setOpenCardId}
                    onMove={setMovingCardId}
                  />
                ))}
              </ul>
              <div className="mt-3">
                <TextForm
                  label={`New card title in ${column.name}`}
                  submitLabel="Add card"
                  placeholder="New card"
                  onSubmit={(title) => addCard(column.id, title)}
                  hideLabel
                  compact
                />
              </div>
            </section>
          ))}
        </div>
      )}

      <AnalyticsPanel analytics={analytics} error={analyticsFailure} />

      <p aria-live="polite" role="status" className="sr-only">
        {liveMessage}
      </p>

      {openCard ? (
        <CardDetailModal
          key={openCard.id}
          card={openCard}
          members={board.members}
          onClose={() => setOpenCardId(null)}
          onUpdated={(card) => {
            replaceCard(card);
            void refetchAnalytics();
          }}
          onDeleted={removeCard}
        />
      ) : null}
      {movingCard ? (
        <CardMoveMenu card={movingCard} board={board} onMove={moveCardTo} onClose={() => setMovingCardId(null)} />
      ) : null}

      <BaseModal open={renamingBoard} title="Rename board" onClose={() => setRenamingBoard(false)}>
        <TextForm label="Board name" submitLabel="Save name" initialValue={board.name} onSubmit={renameBoard} />
      </BaseModal>
      <BaseModal open={addingMember} title="Add member" onClose={() => setAddingMember(false)}>
        <TextForm label="Member email" submitLabel="Add member" placeholder="person@example.com" onSubmit={addMember} />
      </BaseModal>
      <ConfirmDialog
        open={deletingBoard}
        title="Delete board"
        message={`Delete "${board.name}" and everything on it? This cannot be undone.`}
        confirmLabel="Delete board"
        onConfirm={deleteBoard}
        onClose={() => setDeletingBoard(false)}
      />
    </div>
  );
}