"use client";

import { useCallback, useEffect, useId, useState, type FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import { useAuth } from "@/context/AuthContext";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { api } from "@/lib/apiClient";
import type { Comment } from "@/types/api";

export interface CommentListProps {
  cardId: string;
}

/** Lists, adds, edits, and deletes comments. Edit and delete render only for the author (FRONT-011). */
export default function CommentList({ cardId }: CommentListProps) {
  const { currentUser } = useAuth();
  const handleError = useErrorHandler();
  const inputId = useId();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [draft, setDraft] = useState("");
  const [draftError, setDraftError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setComments(await api.get<Comment[]>(`/api/cards/${cardId}/comments`));
    } catch (error) {
      handleError(error);
    } finally {
      setLoaded(true);
    }
  }, [cardId, handleError]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function addComment(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) {
      setDraftError("Write a comment first.");
      return;
    }
    setDraftError(null);
    setBusy(true);
    try {
      const created = await api.post<Comment>(`/api/cards/${cardId}/comments`, { content: draft.trim() });
      setComments((current) => [...current, created]);
      setDraft("");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function saveEdit(commentId: string) {
    if (!editText.trim()) return;
    setBusy(true);
    try {
      const updated = await api.patch<Comment>(`/api/comments/${commentId}`, { content: editText.trim() });
      setComments((current) => current.map((item) => (item.id === commentId ? updated : item)));
      setEditingId(null);
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function remove(commentId: string) {
    try {
      await api.delete(`/api/comments/${commentId}`);
      setComments((current) => current.filter((item) => item.id !== commentId));
    } catch (error) {
      handleError(error);
    }
  }

  return (
    <section aria-labelledby={`${inputId}-title`} className="mt-6">
      <h3 id={`${inputId}-title`} className="text-sm font-semibold text-slate-900">
        Comments
      </h3>
      {!loaded ? (
        <p role="status" className="mt-2 text-sm text-slate-500">
          Loading comments
        </p>
      ) : comments.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No comments yet.</p>
      ) : (
        <ul className="mt-2 space-y-3">
          {comments.map((comment) => {
            const mine = comment.author.id === currentUser?.id;
            return (
              <li key={comment.id} data-testid="comment" className="rounded-md bg-slate-50 p-3 text-sm">
                <p className="text-xs text-slate-500">
                  {comment.author.name} · {comment.created_at.slice(0, 16).replace("T", " ")} UTC
                  {comment.updated_at !== comment.created_at ? " · edited" : ""}
                </p>
                {editingId === comment.id ? (
                  <div className="mt-2 space-y-2">
                    <label htmlFor={`edit-${comment.id}`} className="sr-only">
                      Edit comment
                    </label>
                    <textarea
                      id={`edit-${comment.id}`}
                      value={editText}
                      onChange={(event) => setEditText(event.target.value)}
                      rows={3}
                      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                    />
                    <div className="flex gap-2">
                      <BaseButton loading={busy} onClick={() => saveEdit(comment.id)}>
                        Save comment
                      </BaseButton>
                      <BaseButton variant="secondary" onClick={() => setEditingId(null)}>
                        Cancel
                      </BaseButton>
                    </div>
                  </div>
                ) : (
                  <p className="mt-1 whitespace-pre-wrap text-slate-800">{comment.content}</p>
                )}
                {mine && editingId !== comment.id ? (
                  <div className="mt-2 flex gap-2">
                    <BaseButton
                      variant="secondary"
                      onClick={() => {
                        setEditingId(comment.id);
                        setEditText(comment.content);
                      }}
                    >
                      Edit
                    </BaseButton>
                    <BaseButton variant="destructive" onClick={() => remove(comment.id)}>
                      Delete
                    </BaseButton>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
      <form onSubmit={addComment} noValidate className="mt-4 space-y-2">
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
          Add a comment
        </label>
        <textarea
          id={inputId}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          aria-invalid={draftError ? true : undefined}
          aria-describedby={draftError ? `${inputId}-error` : undefined}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-indigo-600"
        />
        {draftError ? (
          <p id={`${inputId}-error`} className="text-sm text-red-700">
            {draftError}
          </p>
        ) : null}
        <BaseButton type="submit" loading={busy}>
          Post comment
        </BaseButton>
      </form>
    </section>
  );
}