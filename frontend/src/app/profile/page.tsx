"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
import { BaseButton } from "@/components/shared/BaseButton";
export default function ProfilePage() { const { token, user } = useAuth(); const [name, setName] = useState(user?.name ?? ""); const [email, setEmail] = useState(user?.email ?? ""); const submit = async (event: React.FormEvent) => { event.preventDefault(); if (token) await apiClient("/users/me", { method: "PATCH", body: JSON.stringify({ name, email }) }, token); }; return <main className="mx-auto max-w-md p-6"><Link className="text-blue-600" href="/">← Dashboard</Link><h1 className="mt-6 text-3xl font-bold">Profile</h1><form className="mt-6 grid gap-4" onSubmit={submit}><input className="rounded border p-3" value={name} onChange={event => setName(event.target.value)} /><input className="rounded border p-3" type="email" value={email} onChange={event => setEmail(event.target.value)} /><BaseButton type="submit">Save changes</BaseButton></form></main>; }
