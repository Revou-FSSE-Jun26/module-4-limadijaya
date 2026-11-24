"use client";

import { useState } from "react";
import ConfirmDialog from "@/components/boards/ConfirmDialog";
import TextForm from "@/components/boards/TextForm";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";
import type { Column } from "@/types/api";

export interface ColumnHeaderProps {
  column: Column;
  cardCount: number;
  index: number;
  total: number;
  isAdministrator: boolean;
  onRename: (name: string) => Promise<void>;
  onToggleDone: (isDone: boolean) => Promise<void>;
  onDelete: () => Promise<void>;
  onMove: (direction: -1 | 1) => void;
}

/** Column name, count, rename and move for every member. Delete and Done/Active only for administrators (FRONT-025). */
export default function ColumnHeader({ column, cardCount, index, total, isAdministrator, onRename, onToggleDone, onDelete, onMove }: ColumnHeaderProps) {
  const [renaming, setRenaming] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="min-w-0 truncate text-sm font-semibold text-slate-900">{column.name}</h3>
        <div className="flex shrink-0 items-center gap-1">
          {column.is_done ? <BaseBadge color="green">Done column</BaseBadge> : null}
          <BaseBadge>{cardCount}</BaseBadge>
        </div>
      </div>
      <div className="flex flex-wrap gap-1">
        <BaseButton variant="secondary" disabled={index === 0} onClick={() => onMove(-1)} aria-label={`Move column ${column.name} left`}>
          ←
        </BaseButton>
        <BaseButton variant="secondary" disabled={index === total - 1} onClick={() => onMove(1)} aria-label={`Move column ${column.name} right`}>
          →
        </BaseButton>
        <BaseButton variant="secondary" onClick={() => setRenaming(true)} aria-label={`Rename column ${column.name}`}>
          Rename
        </BaseButton>
        {isAdministrator ? (
          <>
            <BaseButton variant="secondary" onClick={() => void onToggleDone(!column.is_done)} aria-label={`Mark column ${column.name} as ${column.is_done ? "active" : "done"}`}>
              {column.is_done ? "Set active" : "Set done"}
            </BaseButton>
            <BaseButton variant="destructive" onClick={() => setConfirmDelete(true)} aria-label={`Delete column ${column.name}`}>
              Delete
            </BaseButton>
          </>
        ) : null}
      </div>
      <BaseModal open={renaming} title="Rename column" onClose={() => setRenaming(false)}>
        <TextForm
          label="Column name"
          submitLabel="Save name"
          initialValue={column.name}
          onSubmit={async (name) => {
            await onRename(name);
            setRenaming(false);
          }}
        />
      </BaseModal>
      <ConfirmDialog
        open={confirmDelete}
        title="Delete column"
        message={`Delete the column "${column.name}"? Its ${cardCount} card(s) will be deleted with it.`}
        confirmLabel="Delete column"
        onConfirm={onDelete}
        onClose={() => setConfirmDelete(false)}
      />
    </div>
  );
}