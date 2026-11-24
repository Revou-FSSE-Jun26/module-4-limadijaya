"use client";

import { useRouter } from "next/navigation";
import TextForm from "@/components/boards/TextForm";
import { api } from "@/lib/apiClient";
import { toastSuccess } from "@/lib/toast";
import type { BoardSummary } from "@/types/api";

/** Creates a board through the proxy, then refreshes the Server Component list (FRONT-005). */
export default function CreateBoardForm() {
  const router = useRouter();
  async function create(name: string) {
    await api.post<BoardSummary>("/api/boards", { name });
    toastSuccess("Board created");
    router.refresh();
  }
  return <TextForm label="Board name" submitLabel="Create board" placeholder="e.g. Website redesign" onSubmit={create} />;
}