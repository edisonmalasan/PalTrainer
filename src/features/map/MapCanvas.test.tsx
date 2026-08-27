import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MapCanvas } from "./MapCanvas";

const invokeMock = vi.hoisted(() => vi.fn());

vi.mock("../../shared/utils/command", () => ({
  invokeCommand: invokeMock,
}));

function mockTilesOk() {
  invokeMock.mockImplementation(async (cmd: string, args?: Record<string, unknown>) => {
    if (cmd === "get_map_asset") {
      const name = args?.name === "treemap-overlay" ? "treemap-overlay" : "world-map";
      return { name, mimeType: "image/png", base64Data: "aWNvbg==" };
    }
    throw new Error(`unexpected command ${cmd}`);
  });
}

const SAMPLE_MARKERS = [
  {
    id: "base_1",
    markerType: "Base",
    label: "HQ",
    worldX: 12000,
    worldY: -85000,
    worldZ: 3200,
    mapX: 10,
    mapY: 20,
  },
  {
    id: "player_1",
    markerType: "Player",
    label: "Host",
    worldX: 15000,
    worldY: -82000,
    worldZ: 3250,
    mapX: -30,
    mapY: 40,
  },
] as const;

describe("MapCanvas", () => {
  beforeEach(() => {
    invokeMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the seven-icon toolbar and requests both tiles", async () => {
    mockTilesOk();
    render(<MapCanvas />);

    expect(
      screen.getByRole("toolbar", { name: "Map view controls" }),
    ).toBeInTheDocument();
    for (const name of [
      "Fit to view",
      "Zoom in",
      "Zoom out",
      "Reset zoom to 100 percent",
      "Toggle treemap overlay",
      "Toggle crosshair",
      "Toggle markers",
    ]) {
      expect(screen.getByRole("button", { name })).toBeInTheDocument();
    }

    await waitFor(() => {
      expect(invokeMock).toHaveBeenCalledWith("get_map_asset", { name: "world-map" });
      expect(invokeMock).toHaveBeenCalledWith("get_map_asset", {
        name: "treemap-overlay",
      });
    });
  });

  it("zooms in, out, and resets from the toolbar", () => {
    mockTilesOk();
    render(<MapCanvas />);

    const zoomLabel = screen.getByTestId("map-zoom-label");
    expect(zoomLabel).toHaveTextContent("100%");

    fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(zoomLabel).toHaveTextContent("125%");

    fireEvent.click(screen.getByRole("button", { name: "Zoom out" }));
    expect(zoomLabel).toHaveTextContent("100%");

    fireEvent.click(screen.getByRole("button", { name: "Reset zoom to 100 percent" }));
    expect(zoomLabel).toHaveTextContent("100%");
  });

  it("reports marker dots and the marker count in the status bar", async () => {
    mockTilesOk();
    render(<MapCanvas markers={SAMPLE_MARKERS} />);

    await waitFor(() => {
      expect(screen.getByTestId("map-markers-layer")).toBeInTheDocument();
    });
    expect(screen.getByTitle("HQ (10, 20)")).toBeInTheDocument();
    expect(screen.getByTitle("Host (-30, 40)")).toBeInTheDocument();
    expect(screen.getByText("2 marker(s)")).toBeInTheDocument();
  });

  it("flips pressed state on the overlay toggles", () => {
    mockTilesOk();
    render(<MapCanvas />);

    const treemap = screen.getByRole("button", { name: "Toggle treemap overlay" });
    const crosshair = screen.getByRole("button", { name: "Toggle crosshair" });
    const markers = screen.getByRole("button", { name: "Toggle markers" });

    expect(treemap).toHaveAttribute("aria-pressed", "false");
    expect(crosshair).toHaveAttribute("aria-pressed", "true");
    expect(markers).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(treemap);
    expect(treemap).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(crosshair);
    expect(crosshair).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(markers);
    expect(markers).toHaveAttribute("aria-pressed", "false");
    expect(screen.queryByTestId("map-markers-layer")).not.toBeInTheDocument();
  });

  it("shows a user-safe error alert when tiles cannot be loaded", async () => {
    invokeMock.mockRejectedValue(
      new Error("Map asset 'world-map.png' is missing from the app resources."),
    );
    render(<MapCanvas />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Map tiles unavailable");
    expect(alert).toHaveTextContent(
      "Map asset 'world-map.png' is missing from the app resources.",
    );
  });
});
