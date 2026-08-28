import { afterEach } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConversionOptionsDialog } from "./ConversionOptionsDialog";
import { DropOverlay } from "./DropOverlay";

// Vitest runs without framework globals, so testing-library's auto-cleanup is
// not registered; clear the DOM between tests to avoid duplicate queries.
afterEach(cleanup);

describe("phase-18 tools pickers", () => {
  it("renders a DropOverlay with the selected file label and browse action", () => {
    const onBrowse = vi.fn();
    const onPickedPath = vi.fn();
    render(
      <DropOverlay
        label="Pick a save file"
        selectedLabel="C:/Saves/World/Level.sav"
        onBrowse={onBrowse}
        onPickedPath={onPickedPath}
      />,
    );

    expect(screen.getByText("Pick a save file")).toBeInTheDocument();
    expect(screen.getByText("C:/Saves/World/Level.sav")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /click to browse or drop/i }));
    expect(onBrowse).toHaveBeenCalledOnce();
  });

  it("opens a 380px conversion options dialog and confirms", () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(
      <ConversionOptionsDialog
        open
        title="SAV to JSON Options"
        pickedFileLabel="C:/Saves/World/Level.sav"
        onConfirm={onConfirm}
        onClose={onClose}
      />,
    );

    // Fixed-width contract: 380px.
    expect(screen.getByTestId("conversion-options-card")).toHaveClass("w-[380px]");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("C:/Saves/World/Level.sav")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Run Conversion/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("closes on Escape when not busy", () => {
    const onConfirm = vi.fn();
    const onClose = vi.fn();
    render(
      <ConversionOptionsDialog
        open
        title="Options"
        onConfirm={onConfirm}
        onClose={onClose}
      />,
    );
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });
});
