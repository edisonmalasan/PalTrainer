import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DestructiveConfirmModal } from "./DestructiveConfirmModal";
import { EmptyState } from "./EmptyState";
import { PreviewModal } from "./PreviewModal";
import { WarningBanner } from "./WarningBanner";

describe("shared safety and state components", () => {
  it("renders empty state actions and invokes the selected action", () => {
    const onOpen = vi.fn();
    const onBrowse = vi.fn();
    render(
      <EmptyState
        headline="No save loaded"
        description="Choose a save file to begin."
        action={{ label: "Open save", onClick: onOpen }}
        secondaryAction={{ label: "Browse", onClick: onBrowse }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open save" }));
    fireEvent.click(screen.getByRole("button", { name: "Browse" }));

    expect(screen.getByRole("heading", { name: "No save loaded" })).toBeInTheDocument();
    expect(onOpen).toHaveBeenCalledOnce();
    expect(onBrowse).toHaveBeenCalledOnce();
  });

  it("exposes warning severity and action through an alert", () => {
    const onReview = vi.fn();
    render(
      <WarningBanner
        severity="destructive"
        title="Save needs attention"
        description="Review the diff before continuing."
        action={{ label: "Review", onClick: onReview }}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Destructive Action");
    expect(screen.getByText("Save needs attention")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Review" }));
    expect(onReview).toHaveBeenCalledOnce();
  });

  it("requires the exact confirmation text before destructive commit", () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(
      <DestructiveConfirmModal
        isOpen
        title="Delete player"
        entityLabel="Player One"
        expectedConfirmationText="DELETE"
        warningMessage="This cannot be undone."
        committing={false}
        onCancel={vi.fn()}
        onConfirm={onConfirm}
      />,
    );

    const confirm = screen.getByRole("button", { name: "Confirm & Destroy" });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Type DELETE/i), {
      target: { value: "delete" },
    });
    expect(confirm).toBeEnabled();
    fireEvent.click(confirm);
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("shows a preview diff and commits with Ctrl+Enter", () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn();
    render(
      <PreviewModal
        preview={{
          operation: "delete_player",
          targetSaveRoot: "C:\\Saves\\World",
          entitiesToModify: [],
          entitiesToDelete: [
            {
              entityType: "player",
              entityId: "player-1",
              label: "Player One",
              changeDescription: "Remove player",
            },
          ],
          filesToModify: ["Players.json"],
          filesToDelete: [],
          backupTarget: "backup.zip",
          warnings: ["A backup will be created."],
          isSafe: true,
        }}
        committing={false}
        onCancel={onCancel}
        onConfirm={onConfirm}
      />,
    );

    expect(screen.getByRole("dialog")).toHaveTextContent("Player One");
    expect(screen.getByText("A backup will be created.")).toBeInTheDocument();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", ctrlKey: true }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });
});
