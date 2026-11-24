"use client";

import { useCallback, useRef, useState, type DragEvent } from "react";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/errors";
import { computeCardOrder, computeColumnOrder, normalizeColumns } from "@/lib/ordering";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import type { BoardDetail, CardMoveResult, Column } from "@/types/api";

export interface UseDragAndDropArgs {
  /** Always returns the latest board, including optimistic changes that have not rendered yet. */
  getBoard: () => BoardDetail;
  commitBoard: (board: BoardDetail) => void;
  refetchBoard: () => Promise<void>;
  announce: (message: string) => void;
  onMoved?: () => void;
}

export interface UseDragAndDropResult {
  draggingCardId: string | null;
  overColumnId: string | null;
  moveCardTo: (cardId: string, destColumnId: string, index: number) => Promise<void>;
  moveColumnTo: (columnId: string, index: number) => Promise<void>;
  cardDragProps: (cardId: string) => {
    draggable: true;
    onDragStart: (event: DragEvent<HTMLElement>) => void;
    onDragEnd: () => void;
  };
  columnDropProps: (columnId: string) => {
    onDragOver: (event: DragEvent<HTMLElement>) => void;
    onDragLeave: () => void;
    onDrop: (event: DragEvent<HTMLElement>) => void;
  };
}

/** Index at which a card dropped at `clientY` belongs, counting the other cards above the pointer. */
export function dropIndexFromPointer(container: HTMLElement, clientY: number, draggedId: string | null): number {
  const items = Array.from(container.querySelectorAll<HTMLElement>("[data-card-id]")).filter(
    (element) => element.dataset.cardId !== draggedId,
  );
  let index = 0;
  for (const element of items) {
    const rect = element.getBoundingClientRect();
    if (clientY > rect.top + rect.height / 2) index += 1;
  }
  return index;
}

/**
 * Native HTML5 drag-and-drop for cards (FE-14). A drop and the keyboard "Move card" menu share
 * moveCardTo: optimistic update, one request in flight at a time, rollback on any error.
 */
export function useDragAndDrop({ getBoard, commitBoard, refetchBoard, announce, onMoved }: UseDragAndDropArgs): UseDragAndDropResult {
  const [draggingCardId, setDraggingCardId] = useState<string | null>(null);
  const [overColumnId, setOverColumnId] = useState<string | null>(null);
  const draggingRef = useRef<string | null>(null);
  const queue = useRef<Promise<void>>(Promise.resolve());
  const handleError = useErrorHandler();

  const runCardMove = useCallback(
    async (cardId: string, destColumnId: string, index: number) => {
      const snapshot = getBoard();
      const source = snapshot.columns.find((column) => column.cards.some((card) => card.id === cardId));
      const dest = snapshot.columns.find((column) => column.id === destColumnId);
      const card = source?.cards.find((item) => item.id === cardId);
      if (!source || !dest || !card) return;

      const others = dest.cards.filter((item) => item.id !== cardId);
      const target = Math.max(0, Math.min(index, others.length));
      if (source.id === dest.id && dest.cards.findIndex((item) => item.id === cardId) === target) return; // same place: no request

      const order = computeCardOrder(others[target - 1]?.order ?? null, others[target]?.order ?? null);
      const moved = { ...card, column_id: dest.id, order };
      commitBoard({
        ...snapshot,
        columns: snapshot.columns.map((column) => {
          if (column.id === dest.id) {
            const next = [...others];
            next.splice(target, 0, moved);
            return { ...column, cards: next };
          }
          if (column.id === source.id) return { ...column, cards: column.cards.filter((item) => item.id !== cardId) };
          return column;
        }),
      });

      try {
        const result = await api.patch<CardMoveResult>(`/api/cards/${cardId}/position`, { column_id: dest.id, order });
        if (result.rebalanced) {
          await refetchBoard();
        } else {
          const latest = getBoard();
          commitBoard({
            ...latest,
            columns: latest.columns.map((column) => ({
              ...column,
              cards: column.cards.map((item) => (item.id === cardId ? { ...item, ...result } : item)),
            })),
          });
        }
        announce(`Card moved to ${dest.name}, position ${target + 1}`);
        onMoved?.();
      } catch (error) {
        commitBoard(snapshot); // revert to the original position
        handleError(error);
        announce("Card could not be moved");
      }
    },
    [getBoard, commitBoard, refetchBoard, announce, onMoved, handleError],
  );

  const moveCardTo = useCallback(
    (cardId: string, destColumnId: string, index: number) => {
      queue.current = queue.current.then(() => runCardMove(cardId, destColumnId, index));
      return queue.current;
    },
    [runCardMove],
  );

  const runColumnMove = useCallback(
    async (columnId: string, index: number) => {
      const snapshot = getBoard();
      const column = snapshot.columns.find((item) => item.id === columnId);
      if (!column) return;
      const others = snapshot.columns.filter((item) => item.id !== columnId);
      const target = Math.max(0, Math.min(index, others.length));
      if (snapshot.columns.findIndex((item) => item.id === columnId) === target) return;

      const single = computeColumnOrder(others[target - 1]?.order ?? null, others[target]?.order ?? null);
      const entries = single === null ? normalizeColumns(snapshot.columns, columnId, target) : [{ id: columnId, order: single }];
      const orderById = new Map(entries.map((entry) => [entry.id, entry.order]));
      const reordered = [...others];
      reordered.splice(target, 0, column);
      commitBoard({
        ...snapshot,
        columns: reordered.map((item) => ({ ...item, order: orderById.get(item.id) ?? item.order })),
      });

      try {
        const result = await api.patch<Column[]>(`/api/boards/${snapshot.id}/columns/reorder`, { columns: entries });
        const latest = getBoard();
        const byId = new Map(latest.columns.map((item) => [item.id, item]));
        commitBoard({
          ...latest,
          columns: result.flatMap((item) => {
            const existing = byId.get(item.id);
            return existing ? [{ ...existing, ...item }] : [];
          }),
        });
        announce(`Column moved to position ${target + 1}`);
      } catch (error) {
        commitBoard(snapshot);
        handleError(error);
        announce("Column could not be moved");
        if (error instanceof ApiError && (error.statusCode === 400 || error.statusCode === 409)) await refetchBoard();
      }
    },
    [getBoard, commitBoard, refetchBoard, announce, handleError],
  );

  const moveColumnTo = useCallback(
    (columnId: string, index: number) => {
      queue.current = queue.current.then(() => runColumnMove(columnId, index));
      return queue.current;
    },
    [runColumnMove],
  );

  const cardDragProps = useCallback(
    (cardId: string) => ({
      draggable: true as const,
      onDragStart: (event: DragEvent<HTMLElement>) => {
        event.dataTransfer.setData("text/plain", cardId); // only the id travels in the drag data
        event.dataTransfer.effectAllowed = "move";
        draggingRef.current = cardId;
        setDraggingCardId(cardId);
      },
      onDragEnd: () => {
        draggingRef.current = null;
        setDraggingCardId(null);
        setOverColumnId(null);
      },
    }),
    [],
  );

  const columnDropProps = useCallback(
    (columnId: string) => ({
      onDragOver: (event: DragEvent<HTMLElement>) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        setOverColumnId(columnId);
      },
      onDragLeave: () => setOverColumnId((current) => (current === columnId ? null : current)),
      onDrop: (event: DragEvent<HTMLElement>) => {
        event.preventDefault();
        const cardId = event.dataTransfer.getData("text/plain") || draggingRef.current;
        draggingRef.current = null;
        setDraggingCardId(null);
        setOverColumnId(null);
        if (!cardId) return;
        void moveCardTo(cardId, columnId, dropIndexFromPointer(event.currentTarget, event.clientY, cardId));
      },
    }),
    [moveCardTo],
  );

  return { draggingCardId, overColumnId, moveCardTo, moveColumnTo, cardDragProps, columnDropProps };
}