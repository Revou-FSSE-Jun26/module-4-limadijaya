"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
interface Comment { id: string; content: string; author_id: string }
export function CommentList({ cardId }: { cardId: string }) { const { token } = useAuth(); const [comments, setComments] = useState<Comment[]>([]); useEffect(() => { if (token) apiClient<Comment[]>(`/cards/${cardId}/comments`, {}, token).then(setComments).catch(() => undefined); }, [cardId, token]); return <ul className="grid gap-2">{comments.map(comment => <li className="rounded bg-gray-50 p-3" key={comment.id}>{comment.content}</li>)}</ul>; }
