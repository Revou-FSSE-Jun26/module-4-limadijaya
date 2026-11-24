import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import BaseModal from "@/components/shared/BaseModal";

describe("BaseButton", () => {
  it("renders each variant and calls onClick", () => {
    const onClick = vi.fn();
    const { rerender } = render(<BaseButton onClick={onClick}>Save</BaseButton>);
    expect(screen.getByRole("button", { name: "Save" }).className).toContain("bg-indigo-600");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    rerender(<BaseButton variant="destructive">Delete</BaseButton>);
    expect(screen.getByRole("button", { name: "Delete" }).className).toContain("bg-red-600");
    rerender(<BaseButton variant="secondary">Cancel</BaseButton>);
    expect(screen.getByRole("button", { name: "Cancel" }).className).toContain("ring-slate-300");
  });
  it("does not fire while loading or disabled", () => {
    const onClick = vi.fn();
    render(
      <BaseButton loading onClick={onClick}>
        Busy
      </BaseButton>,
    );
    const button = screen.getByRole("button", { name: "Busy" });
    expect((button as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("BaseBadge", () => {
  it("applies the color variant", () => {
    render(<BaseBadge color="green">Done</BaseBadge>);
    expect(screen.getByText("Done").className).toContain("bg-green-100");
  });
});

describe("BaseModal", () => {
  it("renders nothing when closed", () => {
    render(
      <BaseModal open={false} title="Hidden" onClose={() => {}}>
        body
      </BaseModal>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("is a labelled modal dialog that closes on Escape and returns focus to the opener", () => {
    const onClose = vi.fn();
    function Harness({ open }: { open: boolean }) {
      return (
        <>
          <a id="opener" href="#top">open</a>
          <BaseModal open={open} title="Rename" onClose={onClose}>
            <input aria-label="Name" />
          </BaseModal>
        </>
      );
    }
    const { rerender } = render(<Harness open={false} />);
    const opener = document.getElementById("opener") as HTMLAnchorElement;
    opener.focus();
    rerender(<Harness open />);
    const dialog = screen.getByRole("dialog", { name: "Rename" });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement).toBe(screen.getByLabelText("Name"));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
    rerender(<Harness open={false} />);
    expect(document.activeElement).toBe(opener);
  });
});