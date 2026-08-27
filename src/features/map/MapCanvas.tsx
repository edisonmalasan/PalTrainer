// Interactive world map canvas for phase 16: pan, cursor-anchored zoom,
// fit-to-view, and a seven-icon toolbar. Raster tiles are served by the
// allowlisted `get_map_asset` command — the canvas never touches the
// filesystem. Marker drag interactions arrive with task 16.2.
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  MapAssetPayload,
  MapMarkerProjection,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

// Placeholder tiles ship at 512x512 and are displayed at 2048x2048.
const MAP_PIXEL_SIZE = 2048;
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 8;
const ZOOM_STEP = 1.25;

interface Vec2 {
  readonly x: number;
  readonly y: number;
}

interface ViewState {
  zoom: number;
  offset: Vec2;
}

function clampZoom(zoom: number): number {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom));
}

// Map grid coordinates are centered on the tile; the grid-to-image-pixel
// calibration is finalized by task 16.4 (sav_to_map_by_z / pixel_to_cursor).
function mapGridToCanvas(grid: number): number {
  return Math.max(0, Math.min(MAP_PIXEL_SIZE, grid + MAP_PIXEL_SIZE / 2));
}

// ── Toolbar icons (inline SVG, 16px, stroke 1.5) ─────────────────────────────

function IconFrame() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M2 5V3.5A1.5 1.5 0 0 1 3.5 2H5M11 2h1.5A1.5 1.5 0 0 1 14 3.5V5M14 11v1.5a1.5 1.5 0 0 1-1.5 1.5H11M5 14H3.5A1.5 1.5 0 0 1 2 12.5V11"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconPlus() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 3v10M3 8h10"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconMinus() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function IconOneToOne() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect
        x="2.5"
        y="2.5"
        width="11"
        height="11"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="M5.5 6.5 7 5.5V10.5M9.5 6h2v4h-2z"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IconLayers() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 2 14 5 8 8 2 5l6-3Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="m2.5 8.5 5.5 2.75 5.5-2.75M2.5 11.5 8 14.25 13.5 11.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconCrosshair() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 1v3.5M8 11.5V15M1 8h3.5M11.5 8H15"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

// ── Canvas ────────────────────────────────────────────────────────────────────

function IconPin() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 14.5S3 9.9 3 6.5a5 5 0 0 1 10 0c0 3.4-5 8-5 8Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="8" cy="6.5" r="1.75" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function MapCanvas({
  markers = [],
}: {
  readonly markers?: readonly MapMarkerProjection[];
}) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{ pointerId: number; start: Vec2; origin: Vec2 } | null>(null);
  const fittedRef = useRef(false);

  const [tiles, setTiles] = useState<{ world: string | null; treemap: string | null }>({
    world: null,
    treemap: null,
  });
  const [tileError, setTileError] = useState<string | null>(null);
  const [view, setView] = useState<ViewState>({ zoom: 1, offset: { x: 0, y: 0 } });
  const [cursor, setCursor] = useState<Vec2 | null>(null);
  const [showTreemap, setShowTreemap] = useState(false);
  const [showCrosshair, setShowCrosshair] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function loadTiles() {
      try {
        const [world, treemap] = await Promise.all([
          invokeCommand<MapAssetPayload>("get_map_asset", { name: "world-map" }),
          invokeCommand<MapAssetPayload>("get_map_asset", { name: "treemap-overlay" }),
        ]);
        if (cancelled) return;
        setTiles({
          world: `data:${world.mimeType};base64,${world.base64Data}`,
          treemap: `data:${treemap.mimeType};base64,${treemap.base64Data}`,
        });
        setTileError(null);
      } catch (error) {
        if (!cancelled) {
          setTileError(
            error instanceof Error ? error.message : "Failed to load map tiles.",
          );
        }
      }
    }
    void loadTiles();
    return () => {
      cancelled = true;
    };
  }, []);

  const fitToView = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const width = viewport.clientWidth;
    const height = viewport.clientHeight;
    if (width <= 0 || height <= 0) return;
    const fit = Math.min(width / MAP_PIXEL_SIZE, height / MAP_PIXEL_SIZE);
    setView({
      zoom: clampZoom(fit),
      offset: {
        x: (width - MAP_PIXEL_SIZE * fit) / 2,
        y: (height - MAP_PIXEL_SIZE * fit) / 2,
      },
    });
  }, []);

  // Fit once the viewport has a measurable size (no-op under jsdom tests).
  useEffect(() => {
    if (fittedRef.current) return;
    const viewport = viewportRef.current;
    if (!viewport) return;
    if (viewport.clientWidth <= 0 || viewport.clientHeight <= 0) return;
    fittedRef.current = true;
    fitToView();
  }, [fitToView]);

  const zoomAt = useCallback((factor: number, anchor: Vec2) => {
    setView((prev) => {
      const zoom = clampZoom(prev.zoom * factor);
      if (zoom === prev.zoom) return prev;
      return {
        zoom,
        offset: {
          x: anchor.x - ((anchor.x - prev.offset.x) / prev.zoom) * zoom,
          y: anchor.y - ((anchor.y - prev.offset.y) / prev.zoom) * zoom,
        },
      };
    });
  }, []);

  const zoomCentered = useCallback(
    (factor: number) => {
      const viewport = viewportRef.current;
      zoomAt(factor, {
        x: (viewport?.clientWidth ?? 0) / 2,
        y: (viewport?.clientHeight ?? 0) / 2,
      });
    },
    [zoomAt],
  );

  const resetZoom = useCallback(() => {
    zoomCentered(1 / view.zoom);
  }, [view.zoom, zoomCentered]);

  function viewportPoint(e: React.PointerEvent | React.WheelEvent): Vec2 {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function handleWheel(e: React.WheelEvent<HTMLDivElement>) {
    e.preventDefault();
    zoomAt(e.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP, viewportPoint(e));
  }

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (e.button !== 0) return;
    dragRef.current = {
      pointerId: e.pointerId,
      start: { x: e.clientX, y: e.clientY },
      origin: view.offset,
    };
    // jsdom has no pointer capture; guard so tests can simulate drag events.
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    setCursor(viewportPoint(e));
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    setView((prev) => ({
      ...prev,
      offset: {
        x: drag.origin.x + (e.clientX - drag.start.x),
        y: drag.origin.y + (e.clientY - drag.start.y),
      },
    }));
  }

  function handlePointerUp(e: React.PointerEvent<HTMLDivElement>) {
    if (dragRef.current?.pointerId === e.pointerId) dragRef.current = null;
  }

  const cursorMap: Vec2 | null = cursor
    ? {
        x: Math.round((cursor.x - view.offset.x) / view.zoom),
        y: Math.round((cursor.y - view.offset.y) / view.zoom),
      }
    : null;

  const toolbarButton =
    "flex h-8 w-8 items-center justify-center border border-shell-line bg-shell-surface text-shell-muted transition-colors hover:bg-shell-panel hover:text-shell-ink";

  return (
    <div className="flex h-full flex-col" data-testid="map-canvas">
      {/* Toolbar — seven controls (fit, zoom in, zoom out, 100%, treemap, crosshair, markers) */}
      <div
        className="flex items-center gap-1 border-b border-shell-line bg-shell-surface px-2 py-1.5"
        role="toolbar"
        aria-label="Map view controls"
      >
        <button
          type="button"
          className={toolbarButton}
          onClick={fitToView}
          title="Fit to view"
          aria-label="Fit to view"
        >
          <IconFrame />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={() => zoomCentered(ZOOM_STEP)}
          title="Zoom in"
          aria-label="Zoom in"
        >
          <IconPlus />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={() => zoomCentered(1 / ZOOM_STEP)}
          title="Zoom out"
          aria-label="Zoom out"
        >
          <IconMinus />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={resetZoom}
          title="Reset zoom to 100%"
          aria-label="Reset zoom to 100 percent"
        >
          <IconOneToOne />
        </button>
        <span className="mx-1 h-5 w-px bg-shell-line" aria-hidden="true" />
        <button
          type="button"
          className={toolbarButton}
          onClick={() => setShowTreemap((v) => !v)}
          title="Toggle treemap overlay"
          aria-label="Toggle treemap overlay"
          aria-pressed={showTreemap}
        >
          <IconLayers />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={() => setShowCrosshair((v) => !v)}
          title="Toggle crosshair"
          aria-label="Toggle crosshair"
          aria-pressed={showCrosshair}
        >
          <IconCrosshair />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={() => setShowMarkers((v) => !v)}
          title="Toggle markers"
          aria-label="Toggle markers"
          aria-pressed={showMarkers}
        >
          <IconPin />
        </button>
        <span
          className="ml-auto pr-1 font-mono text-[11px] text-shell-muted"
          data-testid="map-zoom-label"
        >
          {Math.round(view.zoom * 100)}%
        </span>
      </div>

      {/* Viewport */}
      <div
        ref={viewportRef}
        className="relative min-h-0 flex-1 cursor-grab touch-none select-none overflow-hidden bg-shell-panel active:cursor-grabbing"
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={() => setCursor(null)}
        role="application"
        aria-label="Interactive world map"
        data-testid="map-viewport"
      >
        <div
          className="absolute left-0 top-0"
          style={{
            width: MAP_PIXEL_SIZE,
            height: MAP_PIXEL_SIZE,
            transform: `translate(${view.offset.x}px, ${view.offset.y}px) scale(${view.zoom})`,
            transformOrigin: "0 0",
          }}
          data-testid="map-world"
        >
          {tiles.world && (
            <img
              src={tiles.world}
              width={MAP_PIXEL_SIZE}
              height={MAP_PIXEL_SIZE}
              alt="World map"
              draggable={false}
              className="block h-full w-full [image-rendering:pixelated]"
            />
          )}
          {showTreemap && tiles.treemap && (
            <img
              src={tiles.treemap}
              width={MAP_PIXEL_SIZE}
              height={MAP_PIXEL_SIZE}
              alt="Treemap overlay"
              draggable={false}
              className="absolute left-0 top-0 h-full w-full [image-rendering:pixelated]"
              data-testid="map-treemap"
            />
          )}
          {showMarkers && (
            <div data-testid="map-markers-layer">
              {markers.map((marker) => (
                <div
                  key={marker.id}
                  className="absolute -translate-x-1/2 -translate-y-1/2"
                  style={{
                    left: mapGridToCanvas(marker.mapX),
                    top: mapGridToCanvas(marker.mapY),
                  }}
                  title={`${marker.label || marker.markerType} (${marker.mapX}, ${marker.mapY})`}
                >
                  <span
                    className={[
                      "block h-2.5 w-2.5 rounded-full border border-shell-line shadow-sm",
                      marker.markerType === "Base"
                        ? "bg-shell-accent"
                        : "bg-shell-warning",
                    ].join(" ")}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Crosshair */}
        {showCrosshair && cursor && (
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden="true"
            data-testid="map-crosshair"
          >
            <div
              className="absolute left-0 right-0 h-px bg-shell-line/70"
              style={{ top: cursor.y }}
            />
            <div
              className="absolute bottom-0 top-0 w-px bg-shell-line/70"
              style={{ left: cursor.x }}
            />
          </div>
        )}

        {/* Tile loading / error states */}
        {!tiles.world && !tileError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="font-mono text-xs uppercase tracking-wide text-shell-muted">
              Loading map tiles…
            </p>
          </div>
        )}
        {tileError && (
          <div
            role="alert"
            className="absolute inset-0 flex items-center justify-center p-6 text-center"
          >
            <div>
              <p className="text-sm font-semibold text-shell-ink">
                Map tiles unavailable
              </p>
              <p className="mt-1 text-sm text-shell-muted">{tileError}</p>
            </div>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t border-shell-line bg-shell-surface px-3 py-1.5 font-mono text-[11px] text-shell-muted">
        <span data-testid="map-cursor-coords">
          {cursorMap ? `MAP ${cursorMap.x} , ${cursorMap.y}` : "MAP — , —"}
        </span>
        <span>{markers.length} marker(s)</span>
      </div>
    </div>
  );
}
