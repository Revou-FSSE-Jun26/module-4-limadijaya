"use client";

import { useState, type FormEvent } from "react";
import CommentList from "@/components/comments/CommentList";
import ConfirmDialog from "@/components/boards/ConfirmDialog";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { api } from "@/lib/apiClient";
import { toastSuccess } from "@/lib/toast";
import type { Card, MemberRef } from "@/types/api";

export interface CardDetailModalProps {
  card: Card;
  members: MemberRef[];
  onClose: () => void;
  onUpdated: (card: Card) => void;
  onDeleted: (cardId: string) => void;
}

/** Card details: title, assignee, delete, and the comment thread, inside BaseModal (FRONT-011). */
export default function CardDetailModal({ card, members, onClose, onUpdated, onDeleted }: CardDetailModalProps) {
  const handleError = useErrorHandler();
  const [title, setTitle] = useState(card.title);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function patch(body: { title?: string; assignee_id?: string | null }) {
    const updated = await api.patch<Card>(`/api/cards/${card.id}`, body);
    onUpdated(updated);
    return updated;
  }

  async function saveTitle(event: FormEvent) {
    event.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) {
      setTitleError("Title is required.");
      return;
    }
    setTitleError(null);
    if (trimmed === card.title) return;
    setSaving(true);
    try {
      await patch({ title: trimmed });
      toastSuccess("Card updated");
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  }

  async function changeAssignee(value: string) {
    try {
      await patch({ assignee_id: value === "" ? null : value });
    } catch (error) {
      handleError(error);
    }
  }

  async function deleteCard() {
    await api.delete(`/api/cards/${card.id}`);
    toastSuccess("Card deleted");
    onDeleted(card.id);
  }

  return (
    <>
      <BaseModal open title="Card details" onClose={onClose} wide>
        <form onSubmit={saveTitle} noValidate className="space-y-2">
          <label htmlFor="card-title" className="block text-sm font-medium text-slate-700">
            Title
          </label>
          <input
            id="card-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            aria-invalid={titleError ? true : undefined}
            aria-describedby={titleError ? "card-title-error" : undefined}
            className="min-h-11 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-indigo-600"
          />
          {titleError ? (
            <p id="card-title-error" className="text-sm text-red-700">
              {titleError}
            </p>
          ) : null}
          <BaseButton type="submit" loading={saving}>
            Save title
          </BaseButton>
        </form>

        <div className="mt-4">
          <label htmlFor="card-assignee" className="block text-sm font-medium text-slate-700">
            Assignee
          </label>
          <select
            id="card-assignee"
            value={card.assignee_id ?? ""}
            onChange={(event) => void changeAssignee(event.target.value)}
            className="mt-1 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">Unassigned</option>
            {members.map((member) => (
              <option key={member.id} value={member.id}>
                {member.name}
              </option>
            ))}
          </select>
          {card.completed_at ? (
            <p className="mt-2">
              <BaseBadge color="green">Done</BaseBadge>
            </p>
          ) : null}
        </div>

        <CommentList cardId={card.id} />

        <div className="mt-6 border-t border-slate-200 pt-4">
          <BaseButton variant="destructive" onClick={() => setConfirmDelete(true)}>
            Delete card
          </BaseButton>
        </div>
      </BaseModal>
      <ConfirmDialog
        open={confirmDelete}
        title="Delete card"
        message="This card will be deleted. Its comments are kept but are no longer shown."
        confirmLabel="Delete card"
        onConfirm={deleteCard}
        onClose={() => setConfirmDelete(false)}
      />
    </>
  );
}