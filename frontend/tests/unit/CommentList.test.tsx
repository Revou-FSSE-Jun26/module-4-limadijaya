import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CommentList from "@/components/comments/CommentList";
import type { Comment } from "@/types/api";

const me = { id: "u1", name: "Ada", email: "ada@example.com" };
const mine: Comment = { id: "c1", card_id: "card", content: "Mine", author: { id: "u1", name: "Ada" }, created_at: "2026-11-24T10:00:00Z", updated_at: "2026-11-24T10:00:00Z" };
const theirs: Comment = { id: "c2", card_id: "card", content: "Theirs", author: { id: "u2", name: "Bo" }, created_at: "2026-11-24T10:01:00Z", updated_at: "2026-11-24T10:01:00Z" };

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() }));
vi.mock("@/lib/apiClient", () => ({ api }));
vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({ currentUser: me }) }));
vi.mock("@/lib/toast", () => ({ toastError: vi.fn(), toastSuccess: vi.fn() }));

describe("CommentList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue([mine, theirs]);
  });

  it("shows edit and delete only on the user's own comments", async () => {
    render(<CommentList cardId="card" />);
    await screen.findByText("Mine");
    expect(screen.getAllByRole("button", { name: "Edit" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Delete" })).toHaveLength(1);
  });

  it("validates before posting and posts to the card comments endpoint", async () => {
    render(<CommentList cardId="card" />);
    await screen.findByText("Mine");
    fireEvent.click(screen.getByRole("button", { name: "Post comment" }));
    expect(await screen.findByText("Write a comment first.")).toBeTruthy();
    expect(api.post).not.toHaveBeenCalled();

    api.post.mockResolvedValue({ ...mine, id: "c3", content: "Fresh" });
    fireEvent.change(screen.getByLabelText("Add a comment"), { target: { value: "  Fresh  " } });
    fireEvent.click(screen.getByRole("button", { name: "Post comment" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/api/cards/card/comments", { content: "Fresh" }));
    expect(await screen.findByText("Fresh")).toBeTruthy();
  });

  it("edits a comment through PATCH", async () => {
    api.patch.mockResolvedValue({ ...mine, content: "Changed", updated_at: "2026-11-24T11:00:00Z" });
    render(<CommentList cardId="card" />);
    await screen.findByText("Mine");
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Edit comment"), { target: { value: "Changed" } });
    fireEvent.click(screen.getByRole("button", { name: "Save comment" }));
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/api/comments/c1", { content: "Changed" }));
    expect(await screen.findByText("Changed")).toBeTruthy();
  });
});