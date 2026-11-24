"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import Field from "@/components/auth/AuthFields";
import BaseButton from "@/components/shared/BaseButton";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/errors";
import { useErrorHandler } from "@/hooks/useErrorHandler";

/** Login form. Success stores the session in AuthContext and goes to the dashboard (FRONT-002). */
export default function LoginForm() {
  const { login } = useAuth();
  const handleError = useErrorHandler();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next: { email?: string; password?: string } = {};
    if (!email.trim()) next.email = "Email is required.";
    if (!password) next.password = "Password is required.";
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length > 0) return;
    setBusy(true);
    try {
      await login(email.trim(), password);
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) {
        setFormError(error.message);
      } else {
        handleError(error);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      {formError ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {formError}
        </p>
      ) : null}
      <Field label="Email" type="email" value={email} onChange={setEmail} error={errors.email} autoComplete="email" />
      <Field label="Password" type="password" value={password} onChange={setPassword} error={errors.password} autoComplete="current-password" />
      <BaseButton type="submit" loading={busy} fullWidth>
        Log in
      </BaseButton>
      <p className="text-center text-sm text-slate-600">
        No account yet?{" "}
        <Link href="/register" className="font-medium text-indigo-700 underline">
          Register
        </Link>
      </p>
    </form>
  );
}