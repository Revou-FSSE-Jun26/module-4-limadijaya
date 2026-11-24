"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
import { BaseButton } from "@/components/shared/BaseButton";
import { BaseBadge } from "@/components/shared/BaseBadge";
interface Board { id: string; name: string }
export default function DashboardPage() {
  const { token, user, logout } = useAuth(); const [boards, setBoards] = useState<Board[]>([]); const [name, setName] = useState("");
  useEffect(() => { if (token) apiClient<Board[]>("/boards", {}, token).then(setBoards).catch(() => undefined); }, [token]);
  if (!token) return <main className="mx-auto max-w-3xl p-6"><h1 className="text-4xl font-bold">RevoTask</h1><p className="mt-2">Organize work, collaborate, and move tasks forward.</p><div className="mt-6 flex gap-3"><Link href="/login"><BaseButton>Log in</BaseButton></Link><Link href="/register"><BaseButton variant="secondary">Register</BaseButton></Link></div></main>;
  const createBoard = async () => { if (!name.trim()) return; const board = await apiClient<Board>("/boards", { method: "POST", body: JSON.stringify({ name }) }, token); setBoards([...boards, board]); setName(""); };
  return <main className="mx-auto max-w-5xl p-6"><header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-3xl font-bold">Your boards</h1><p className="text-gray-600">Welcome, {user?.name}</p></div><nav className="flex items-center gap-2"><Link href="/my-tasks"><BaseBadge>My Tasks</BaseBadge></Link><Link href="/profile"><BaseBadge variant="gray">Profile</BaseBadge></Link><BaseButton variant="secondary" onClick={logout}>Log out</BaseButton></nav></header><section className="mt-8 flex gap-2"><input className="rounded border p-2" placeholder="New board name" value={name} onChange={event => setName(event.target.value)} /><BaseButton onClick={createBoard}>Create board</BaseButton></section><section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{boards.map(board => <Link href={`/boards/${board.id}`} key={board.id} className="rounded border bg-white p-5 shadow-sm hover:border-blue-500"><h2 className="font-semibold">{board.name}</h2><p className="mt-2 text-sm text-gray-500">Open board</p></Link>)}</section></main>;
}
