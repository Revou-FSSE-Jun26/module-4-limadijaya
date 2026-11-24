import toast from "react-hot-toast";

/** Thin wrapper over react-hot-toast so components never import the library directly (FE-07). */
export function toastSuccess(message: string): string {
  return toast.success(message);
}

export function toastError(message: string): string {
  return toast.error(message);
}

export function toastLoading(message: string): string {
  return toast.loading(message);
}

export function dismissToast(id?: string): void {
  toast.dismiss(id);
}
