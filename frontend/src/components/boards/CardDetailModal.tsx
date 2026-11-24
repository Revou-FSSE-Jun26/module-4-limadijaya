"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
import { BaseButton } from "@/components/shared/BaseButton";
import { BaseModal } from "@/components/shared/BaseModal";
import { CommentList } from "@/components/comments/CommentList";
export function CardDetailModal({ cardId, title, open, onClose }: { cardId: string; title: string; open: boolean; onClose: () => void }) { const { token } = useAuth(); const [content, setContent] = useState(""); const submit = async (event: React.FormEvent) => { event.preventDefault(); if (token && content.trim()) { await apiClient(`/cards/${cardId}/comments`, { method: "POST", body: JSON.stringify({ content }) }, token); setContent(""); } }; return <BaseModal open={open} title={title} onClose={onClose}><CommentList cardId={cardId} /><form className="mt-4 flex gap-2" onSubmit={submit}><input className="min-w-0 flex-1 rounded border p-2" value={content} onChange={event => setContent(event.target.value)} placeholder="Add a comment" /><BaseButton type="submit">Comment</BaseButton></form></BaseModal>; }
