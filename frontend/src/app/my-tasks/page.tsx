"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
export default function MyTasksPage() { const { token } = useAuth(); const [cards, setCards] = useState<{ id: string; title: string }[]>([]); useEffect(() => { if (token) apiClient<{ id: string; title: string }[]>("/cards?assignee=me", {}, token).then(setCards).catch(() => undefined); }, [token]); return <main className="mx-auto max-w-3xl p-6"><Link className="text-blue-600" href="/">← Dashboard</Link><h1 className="mt-6 text-3xl font-bold">My Tasks</h1><ul className="mt-6 grid gap-3">{cards.map(card => <li className="rounded border p-4" key={card.id}>{card.title}</li>)}</ul></main>; }
