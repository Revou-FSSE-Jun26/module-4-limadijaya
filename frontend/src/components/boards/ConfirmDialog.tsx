"use client";

import { useState } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";
import { useErrorHandler } from "@/hooks/useErrorHandler";

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
}

/** A destructive confirmation built on BaseModal. */
export default function ConfirmDialog({ open, title, message, confirmLabel, onConfirm, onClose }: ConfirmDialogProps) {
  const [busy, setBusy] = useState(false);
  const handleError = useErrorHandler();
  async function confirm() {
    setBusy(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }
  return (
    <BaseModal open={open} title={title} onClose={onClose}>
      <p className="text-sm text-slate-700">{message}</p>
      <div className="mt-4 flex justify-end gap-2">
        <BaseButton variant="secondary" onClick={onClose}>
          Cancel
        </BaseButton>
        <BaseButton variant="destructive" loading={busy} onClick={confirm}>
          {confirmLabel}
        </BaseButton>
      </div>
    </BaseModal>
  );
}