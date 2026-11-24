import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PlaceholderPage from "@/app/page";

// Trivial test that proves the Vitest + React Testing Library setup works (T1.06).
describe("placeholder page", () => {
  it("renders the RevoTask heading", () => {
    render(<PlaceholderPage />);
    expect(screen.getByRole("heading", { name: "RevoTask" })).toBeDefined();
  });
});
