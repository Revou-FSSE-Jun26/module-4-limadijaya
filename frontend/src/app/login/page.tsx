"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { BaseButton } from "@/components/shared/BaseButton";
import { useAuth } from "@/context/AuthContext";
import { apiClient } from "@/lib/apiClient";
export default function LoginPage() { const router = useRouter(); const { setSession } = useAuth(); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const submit = async (event: React.FormEvent) => { event.preventDefault(); try { const result = await apiClient<{ access_token: string; user: { id: string; name: string; email: string } }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); setSession(result.access_token, result.user); router.push("/"); } catch (value) { setError(value instanceof Error ? value.message : "Login failed."); } }; return <main className="mx-auto max-w-md p-6"><h1 className="text-3xl font-bold">Log in</h1><form className="mt-6 grid gap-4" onSubmit={submit}><input className="rounded border p-3" type="email" placeholder="Email" value={email} onChange={event => setEmail(event.target.value)} required /><input className="rounded border p-3" type="password" placeholder="Password" value={password} onChange={event => setPassword(event.target.value)} required /><BaseButton type="submit">Log in</BaseButton>{error && <p className="text-red-600">{error}</p>}</form><p className="mt-4">New here? <Link className="text-blue-600" href="/register">Create an account</Link></p></main>; }
