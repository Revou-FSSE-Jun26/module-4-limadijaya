"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import Field from "@/components/auth/AuthFields";
import BaseButton from "@/components/shared/BaseButton";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/errors";
import { toastSuccess } from "@/lib/toast";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import type { UserPublic } from "@/types/api";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** Registration form with client-side validation. Success goes to /login with a toast (FRONT-001). */
export default function RegisterForm() {
  const router = useRouter();
  const handleError = useErrorHandler();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next: { name?: string; email?: string; password?: string } = {};
    if (!name.trim()) next.name = "Name is required.";
    if (!email.trim()) next.email = "Email is required.";
    else if (!EMAIL_PATTERN.test(email.trim())) next.email = "Enter a valid email address.";
    if (!password) next.password = "Password is required.";
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length > 0) return;
    setBusy(true);
    try {
      await api.post<UserPublic>("/api/auth/register", { name: name.trim(), email: email.trim(), password });
      toastSuccess("Account created. Please log in.");
      router.push("/login");
    } catch (error) {
      if (error instanceof ApiError && (error.statusCode === 409 || error.statusCode === 400)) {
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
      <Field label="Name" value={name} onChange={setName} error={errors.name} autoComplete="name" />
      <Field label="Email" type="email" value={email} onChange={setEmail} error={errors.email} autoComplete="email" />
      <Field label="Password" type="password" value={password} onChange={setPassword} error={errors.password} autoComplete="new-password" />
      <BaseButton type="submit" loading={busy} fullWidth>
        Create account
      </BaseButton>
      <p className="text-center text-sm text-slate-600">
        Already registered?{" "}
        <Link href="/login" className="font-medium text-indigo-700 underline">
          Log in
        </Link>
      </p>
    </form>
  );
}