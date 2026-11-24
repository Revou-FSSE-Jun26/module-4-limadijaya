"use client";

import { useId, useState, type FormEvent } from "react";
import BaseButton from "@/components/shared/BaseButton";
import { useErrorHandler } from "@/hooks/useErrorHandler";

export interface TextFormProps {
  label: string;
  submitLabel: string;
  placeholder?: string;
  initialValue?: string;
  onSubmit: (value: string) => Promise<void>;
  /** Hide the visible label and keep it for screen readers (inline forms). */
  hideLabel?: boolean;
  compact?: boolean;
}

/** One controlled text input with a submit button. Used by every "add" and "rename" form. */
export default function TextForm({ label, submitLabel, placeholder, initialValue = "", onSubmit, hideLabel = false, compact = false }: TextFormProps) {
  const id = useId();
  const errorId = useId();
  const [value, setValue] = useState(initialValue);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const handleError = useErrorHandler();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) {
      setFieldError(`${label} is required.`);
      return;
    }
    setFieldError(null);
    setBusy(true);
    try {
      await onSubmit(trimmed);
      setValue(initialValue);
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className={compact ? "space-y-2" : "space-y-3"}>
      <div>
        <label htmlFor={id} className={hideLabel ? "sr-only" : "mb-1 block text-sm font-medium text-slate-700"}>
          {label}
        </label>
        <input
          id={id}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          aria-invalid={fieldError ? true : undefined}
          aria-describedby={fieldError ? errorId : undefined}
          className="min-h-11 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-indigo-600"
        />
        {fieldError ? (
          <p id={errorId} className="mt-1 text-sm text-red-700">
            {fieldError}
          </p>
        ) : null}
      </div>
      <BaseButton type="submit" loading={busy}>
        {submitLabel}
      </BaseButton>
    </form>
  );
}