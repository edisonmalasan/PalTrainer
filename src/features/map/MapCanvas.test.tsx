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
    areaRange: 1.0,
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
    expect(screen.getByTestId("map-marker-base_1")).toBeInTheDocument();
    expect(screen.getByTestId("map-marker-player_1")).toBeInTheDocument();
    expect(screen.getByText("2 marker(s)")).toBeInTheDocument();
  });

  it("drags a base marker and reports the new map grid position", async () => {
    mockTilesOk();
    const onMoveMarker = vi.fn();
    render(<MapCanvas markers={SAMPLE_MARKERS} onMoveMarker={onMoveMarker} />);

    const marker = await screen.findByTestId("map-marker-base_1");
    // Initial layer position is (mapX + 1024, mapY + 1024) = (1034, 1044).
    fireEvent.pointerDown(marker, {
      button: 0,
      pointerId: 1,
      clientX: 1034,
      clientY: 1044,
    });
    fireEvent.pointerMove(marker, { pointerId: 1, clientX: 1074, clientY: 1054 });
    fireEvent.pointerUp(marker, { pointerId: 1, clientX: 1074, clientY: 1054 });

    expect(onMoveMarker).toHaveBeenCalledOnce();
    const [moved, mapX, mapY] = onMoveMarker.mock.calls[0];
    expect(moved.id).toBe("base_1");
    expect(mapX).toBe(50); // 10 + 40px drag
    expect(mapY).toBe(30); // 20 + 10px drag
  });

  it("drags the base radius ring and reports a clamped area range", async () => {
    mockTilesOk();
    const onAreaRangeChange = vi.fn();
    const base = { ...SAMPLE_MARKERS[0], areaRange: 1.0 };
    render(<MapCanvas markers={[base]} onAreaRangeChange={onAreaRangeChange} />);

    const handle = await screen.findByTestId("map-ring-handle-base_1");
    // Ring radius at 1.0 is 24 grid units; handle starts at layer x 1058.
    fireEvent.pointerDown(handle, {
      button: 0,
      pointerId: 1,
      clientX: 1058,
      clientY: 1044,
    });
    // Drag 48px from the center -> radius 48 -> 2.0x area range.
    fireEvent.pointerMove(handle, { pointerId: 1, clientX: 1082, clientY: 1044 });
    fireEvent.pointerUp(handle, { pointerId: 1, clientX: 1082, clientY: 1044 });

    expect(onAreaRangeChange).toHaveBeenCalledOnce();
    expect(onAreaRangeChange.mock.calls[0][0].id).toBe("base_1");
    expect(onAreaRangeChange.mock.calls[0][1]).toBe(2);

    // Oversized drags clamp to the save-format maximum (10.0).
    cleanup();
    const onClamped = vi.fn();
    render(<MapCanvas markers={[base]} onAreaRangeChange={onClamped} />);
    const handle2 = screen.getByTestId("map-ring-handle-base_1");
    fireEvent.pointerDown(handle2, {
      button: 0,
      pointerId: 2,
      clientX: 1058,
      clientY: 1044,
    });
    fireEvent.pointerMove(handle2, { pointerId: 2, clientX: 2058, clientY: 1044 });
    fireEvent.pointerUp(handle2, { pointerId: 2, clientX: 2058, clientY: 1044 });
    expect(onClamped.mock.calls[0][1]).toBe(10);
  });

  it("shows the hover overlay with marker details", async () => {
    mockTilesOk();
    render(<MapCanvas markers={SAMPLE_MARKERS} />);

    const marker = await screen.findByTestId("map-marker-base_1");
    fireEvent.mouseEnter(marker);

    const overlay = screen.getByTestId("map-hover-overlay");
    expect(overlay).toHaveTextContent("Base");
    expect(overlay).toHaveTextContent("HQ");
    expect(overlay).toHaveTextContent("MAP 10 , 20");
    expect(overlay).toHaveTextContent("AREA 100%");

    fireEvent.mouseLeave(marker);
    expect(screen.queryByTestId("map-hover-overlay")).not.toBeInTheDocument();
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
