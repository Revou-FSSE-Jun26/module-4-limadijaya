"use client";

import type { DragEvent } from "react";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import { cx } from "@/lib/cx";
import type { Card } from "@/types/api";

export interface CardItemProps {
  card: Card;
  assigneeName: string | null;
  dragging: boolean;
  hidden: boolean;
  dragProps: {
    draggable: true;
    onDragStart: (event: DragEvent<HTMLElement>) => void;
    onDragEnd: () => void;
  };
  onOpen: (cardId: string) => void;
  onMove: (cardId: string) => void;
}

/** A draggable card tile. A search filter only hides it, so ordering still sees every card (FRONT-019-AC07). */
export default function CardItem({ card, assigneeName, dragging, hidden, dragProps, onOpen, onMove }: CardItemProps) {
  return (
    <li
      data-card-id={card.id}
      data-testid="card"
      hidden={hidden}
      {...dragProps}
      className={cx(
        "cursor-grab rounded-md border border-slate-200 bg-white p-3 shadow-sm active:cursor-grabbing",
        dragging && "opacity-50",
        hidden && "hidden",
      )}
    >
      <BaseButton variant="secondary" fullWidth onClick={() => onOpen(card.id)} aria-label={`Open card ${card.title}`}>
        <span className="truncate text-left">{card.title}</span>
      </BaseButton>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1">
          {assigneeName ? <BaseBadge color="blue">{assigneeName}</BaseBadge> : null}
          {card.completed_at ? <BaseBadge color="green">Done</BaseBadge> : null}
        </div>
        <BaseButton variant="secondary" onClick={() => onMove(card.id)} aria-label={`Move card ${card.title}`}>
          Move
        </BaseButton>
      </div>
    </li>
  );
}