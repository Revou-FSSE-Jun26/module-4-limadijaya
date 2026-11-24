"use client";

import { useState, type FormEvent } from "react";
import Field from "@/components/auth/AuthFields";
import BaseButton from "@/components/shared/BaseButton";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/errors";
import { toastSuccess } from "@/lib/toast";
import { useErrorHandler } from "@/hooks/useErrorHandler";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** Updates name and email only. There is no password field (FRONT-010). */
export default function ProfileForm() {
  const { currentUser, updateProfile } = useAuth();
  const handleError = useErrorHandler();
  const [name, setName] = useState(currentUser?.name ?? "");
  const [email, setEmail] = useState(currentUser?.email ?? "");
  const [errors, setErrors] = useState<{ name?: string; email?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next: { name?: string; email?: string } = {};
    if (!name.trim()) next.name = "Name is required.";
    if (!email.trim()) next.email = "Email is required.";
    else if (!EMAIL_PATTERN.test(email.trim())) next.email = "Enter a valid email address.";
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length > 0) return;
    setBusy(true);
    try {
      await updateProfile({ name: name.trim(), email: email.trim() });
      toastSuccess("Profile updated");
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
    <form onSubmit={onSubmit} noValidate className="max-w-md space-y-4">
      {formError ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {formError}
        </p>
      ) : null}
      <Field label="Name" value={name} onChange={setName} error={errors.name} autoComplete="name" />
      <Field label="Email" type="email" value={email} onChange={setEmail} error={errors.email} autoComplete="email" />
      <BaseButton type="submit" loading={busy}>
        Save profile
      </BaseButton>
    </form>
  );
}