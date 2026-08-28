import { afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ToolsView } from "./ToolsView";

// Vitest runs without framework globals, so testing-library's auto-cleanup is
// not registered; clear the DOM between tests to avoid duplicate queries.
afterEach(cleanup);

// The phase-18 outcome: Conversion Tools 2×2 + Management Tools grid with
// `rounded-[2.5rem]` cards and descriptions under each label.
describe("ToolsView bento grid", () => {
  it("renders both tool grids with rounded cards and descriptions", () => {
    render(<ToolsView />);

    expect(
      screen.getByRole("heading", { name: "Conversion Tools" }),
    ).toBeInTheDocument();
    for (const card of [
      "Convert Save Files",
      "GamePass ↔ Steam",
      "SteamID Convert",
      "Restore Map",
    ]) {
      // Cards are uniquely tagged (tab labels can share names, e.g. the
      // "Character Transfer" tab), so query by data attribute.
      const button = screen.getByRole("button", {
        name: new RegExp(card),
      });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass("rounded-[2.5rem]");
    }

    // Management Tools grid.
    expect(
      screen.getByRole("heading", { name: "Management Tools" }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("tool-card-Slot Injector")).toBeInTheDocument();
    expect(screen.getByTestId("tool-card-Character Transfer")).toBeInTheDocument();
    expect(screen.getByTestId("tool-card-Fix Host Save")).toBeInTheDocument();
  });

  it("renders the converter panel below the grids", () => {
    render(<ToolsView />);
    // The converter tab always mounts the panel beneath the landing grids.
    expect(
      screen.getByRole("heading", { name: /Format Converter/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Identifier Calculator/i }),
    ).toBeInTheDocument();
  });

  it("lists each tool card with its description underneath", () => {
    render(<ToolsView />);
    expect(
      screen.getByText("SAV to JSON and back, with PLZ / CNK compression"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Reveal world fog and hidden locations in LocalData.sav"),
    ).toBeInTheDocument();
  });
});
