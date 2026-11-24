import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CardSearchInput from "@/components/boards/CardSearchInput";

describe("CardSearchInput", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("reports the term only after 300 ms without typing", () => {
    const onTermChange = vi.fn();
    render(<CardSearchInput onTermChange={onTermChange} />);
    onTermChange.mockClear();
    fireEvent.change(screen.getByLabelText("Search cards"), { target: { value: "rev" } });
    act(() => vi.advanceTimersByTime(299));
    expect(onTermChange).not.toHaveBeenCalledWith("rev");
    act(() => vi.advanceTimersByTime(1));
    expect(onTermChange).toHaveBeenCalledWith("rev");
  });

  it("restarts the timer on every keystroke", () => {
    const onTermChange = vi.fn();
    render(<CardSearchInput onTermChange={onTermChange} />);
    const input = screen.getByLabelText("Search cards");
    fireEvent.change(input, { target: { value: "r" } });
    act(() => vi.advanceTimersByTime(200));
    fireEvent.change(input, { target: { value: "re" } });
    act(() => vi.advanceTimersByTime(200));
    expect(onTermChange).not.toHaveBeenCalledWith("re");
    act(() => vi.advanceTimersByTime(100));
    expect(onTermChange).toHaveBeenCalledWith("re");
    expect(onTermChange).not.toHaveBeenCalledWith("r");
  });
});