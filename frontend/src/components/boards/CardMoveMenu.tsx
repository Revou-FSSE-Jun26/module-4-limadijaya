"use client";

import { useId, useState } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";
import type { BoardDetail, Card } from "@/types/api";

export interface CardMoveMenuProps {
  card: Card;
  board: BoardDetail;
  onMove: (cardId: string, destColumnId: string, index: number) => Promise<void>;
  onClose: () => void;
}

/** Keyboard and touch alternative to dragging (DA-18): choose a column and a place, then confirm. */
export default function CardMoveMenu({ card, board, onMove, onClose }: CardMoveMenuProps) {
  const columnId = useId();
  const placeId = useId();
  const [destination, setDestination] = useState(card.column_id);
  const [place, setPlace] = useState("0");
  const dest = board.columns.find((column) => column.id === destination);
  const others = (dest?.cards ?? []).filter((item) => item.id !== card.id);

  async function confirm() {
    onClose();
    await onMove(card.id, destination, Number(place));
  }

  return (
    <BaseModal open title={`Move card: ${card.title}`} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label htmlFor={columnId} className="block text-sm font-medium text-slate-700">
            Column
          </label>
          <select
            id={columnId}
            value={destination}
            onChange={(event) => {
              setDestination(event.target.value);
              setPlace("0");
            }}
            className="mt-1 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {board.columns.map((column) => (
              <option key={column.id} value={column.id}>
                {column.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor={placeId} className="block text-sm font-medium text-slate-700">
            Place
          </label>
          <select
            id={placeId}
            value={place}
            onChange={(event) => setPlace(event.target.value)}
            className="mt-1 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            <option value="0">Top of column</option>
            {others.map((other, index) => (
              <option key={other.id} value={String(index + 1)}>
                After {other.title}
              </option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-2">
          <BaseButton variant="secondary" onClick={onClose}>
            Cancel
          </BaseButton>
          <BaseButton onClick={confirm}>Move card</BaseButton>
        </div>
      </div>
    </BaseModal>
  );
}