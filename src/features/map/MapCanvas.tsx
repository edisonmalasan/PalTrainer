// Interactive world map canvas for phase 16: pan, cursor-anchored zoom,
// fit-to-view, and a seven-icon toolbar. Raster tiles are served by the
// allowlisted `get_map_asset` command — the canvas never touches the
// filesystem. Marker drag interactions arrive with task 16.2.
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  MapAssetPayload,
  MapMarkerProjection,
  Point2D,
  ZoneExclusion,
} from "../../shared/types/contracts";
import { invokeCommand } from "../../shared/utils/command";

// Placeholder tiles ship at 512x512 and are displayed at 2048x2048.
const MAP_PIXEL_SIZE = 2048;
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 8;
const ZOOM_STEP = 1.25;

// Presentation placeholder until 16.4 calibration: ring radius in map grid
// units per 1.0 of area_range. The backend stays the authority for saved
// values; bounds mirror `base_camp::MIN/MAX_AREA_RANGE` for inline feedback.
const BASE_RING_GRID_UNITS = 24;
const MIN_AREA_RANGE = 0.5;
const MAX_AREA_RANGE = 10.0;

interface Vec2 {
  readonly x: number;
  readonly y: number;
}

// Zone drawing modes (task 16.3): rectangle drag + polygon vertex placement.
type ZoneDrawMode = "none" | "rectangle" | "polygon";
type ZoneGeometry = "rectangle" | "polygon";

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

// ── Hover overlay ─────────────────────────────────────────────────────────────

function HoverOverlay({ marker }: { readonly marker: MapMarkerProjection | null }) {
  if (!marker) return null;
  return (
    <div
      className="pointer-events-none absolute right-3 top-3 max-w-[240px] border border-shell-line bg-shell-surface/95 px-3 py-2 shadow-sm"
      data-testid="map-hover-overlay"
    >
      <p className="font-mono text-[10px] uppercase tracking-wide text-shell-muted">
        {marker.markerType}
      </p>
      <p className="mt-0.5 truncate text-sm font-semibold text-shell-ink">
        {marker.label || marker.id}
      </p>
      <p className="mt-0.5 font-mono text-[11px] leading-5 text-shell-muted">
        {marker.mapVersion} · MAP {marker.mapX} , {marker.mapY}
        <br />
        WORLD {marker.worldX.toFixed(0)} , {marker.worldY.toFixed(0)} ,{" "}
        {marker.worldZ.toFixed(0)}
        <br />
        TREE {marker.treemapX} , {marker.treemapY}
        {marker.areaRange != null && (
          <>
            <br />
            AREA {Math.round(marker.areaRange * 100)}%
          </>
        )}
      </p>
    </div>
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

function IconRect() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect
        x="2.5"
        y="4.5"
        width="11"
        height="7"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeDasharray="3 2"
      />
    </svg>
  );
}

function IconPolygon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M8 2.5 13.5 6.5 11.5 13h-7L2.5 6.5 8 2.5Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ── Zone overlays ────────────────────────────────────────────────────────────

function mapGridToCanvasPoint(p: Vec2): Vec2 {
  return { x: mapGridToCanvas(p.x), y: mapGridToCanvas(p.y) };
}

// Renders one exclusion zone (or the in-progress draft) as a world-layer SVG
// shape. Two corner points render as a rectangle, three or more as a polygon.
function ZoneShapeSvg({
  corners,
  draft,
  testId,
}: {
  readonly corners: readonly Vec2[];
  readonly draft: boolean;
  readonly testId: string;
}) {
  const canvasPts = corners.map(mapGridToCanvasPoint);
  const xs = canvasPts.map((p) => p.x);
  const ys = canvasPts.map((p) => p.y);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  return (
    <svg
      className={[
        "pointer-events-none absolute left-0 top-0 overflow-visible",
        draft ? "text-shell-accent" : "text-shell-warning",
      ].join(" ")}
      width={1}
      height={1}
      data-testid={testId}
    >
      {canvasPts.length === 2 ? (
        <rect
          x={minX}
          y={minY}
          width={Math.max(...xs) - minX}
          height={Math.max(...ys) - minY}
          fill="currentColor"
          fillOpacity={0.1}
          stroke="currentColor"
          strokeWidth={1.5}
          strokeDasharray={draft ? "6 4" : undefined}
        />
      ) : (
        <polygon
          points={canvasPts.map((p) => `${p.x},${p.y}`).join(" ")}
          fill="currentColor"
          fillOpacity={0.1}
          stroke="currentColor"
          strokeWidth={1.5}
          strokeDasharray={draft ? "6 4" : undefined}
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

export function MapCanvas({
  markers = [],
  zones = [],
  onMoveMarker,
  onAreaRangeChange,
  onZoneDrawn,
}: {
  readonly markers?: readonly MapMarkerProjection[];
  readonly zones?: readonly ZoneExclusion[];
  readonly onMoveMarker?: (
    marker: MapMarkerProjection,
    mapX: number,
    mapY: number,
  ) => void;
  readonly onAreaRangeChange?: (marker: MapMarkerProjection, areaRange: number) => void;
  readonly onZoneDrawn?: (zoneType: ZoneGeometry, points: readonly Point2D[]) => void;
}) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{
    pointerId: number;
    mode: "pan" | "move" | "ring";
    start: Vec2;
    origin: Vec2;
    marker: MapMarkerProjection | null;
    originLayer: Vec2;
  } | null>(null);
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
  const [dragMarkerId, setDragMarkerId] = useState<string | null>(null);
  const [dragPos, setDragPos] = useState<Vec2 | null>(null);
  const [ringRange, setRingRange] = useState<number | null>(null);
  const [hoveredMarkerId, setHoveredMarkerId] = useState<string | null>(null);
  const [drawMode, setDrawMode] = useState<ZoneDrawMode>("none");
  const [draftPoints, setDraftPoints] = useState<Vec2[] | null>(null);
  const rectStartRef = useRef<Vec2 | null>(null);

  // Escape cancels an in-progress zone draft (rect corners or polygon vertices).
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      rectStartRef.current = null;
      setDraftPoints(null);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

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

  function clampAreaRange(range: number): number {
    const stepped = Math.round(range * 10) / 10;
    return Math.min(MAX_AREA_RANGE, Math.max(MIN_AREA_RANGE, stepped));
  }

  function toggleDraw(mode: Exclude<ZoneDrawMode, "none">) {
    setDrawMode((prev) => (prev === mode ? "none" : mode));
    rectStartRef.current = null;
    setDraftPoints(null);
  }

  // Viewport pointer position -> map-grid units (inverse of mapGridToCanvas).
  function eventToGrid(e: React.PointerEvent<HTMLDivElement>): Vec2 {
    const point = viewportPoint(e);
    return {
      x: Math.round((point.x - view.offset.x) / view.zoom - MAP_PIXEL_SIZE / 2),
      y: Math.round((point.y - view.offset.y) / view.zoom - MAP_PIXEL_SIZE / 2),
    };
  }

  function markerLayerPos(marker: MapMarkerProjection): Vec2 {
    if (dragMarkerId === marker.id && dragPos) return dragPos;
    return { x: mapGridToCanvas(marker.mapX), y: mapGridToCanvas(marker.mapY) };
  }

  function beginMarkerDrag(
    e: React.PointerEvent<HTMLElement>,
    marker: MapMarkerProjection,
    mode: "move" | "ring",
  ) {
    if (e.button !== 0) return;
    // Keep the viewport pan handler out of marker drags.
    e.stopPropagation();
    const pos = markerLayerPos(marker);
    dragRef.current = {
      pointerId: e.pointerId,
      mode,
      start: { x: e.clientX, y: e.clientY },
      origin: view.offset,
      marker,
      originLayer: pos,
    };
    setDragMarkerId(marker.id);
    setHoveredMarkerId(null);
    if (mode === "move") setDragPos(pos);
    if (mode === "ring") setRingRange(clampAreaRange(marker.areaRange ?? 1.0));
    // jsdom has no pointer capture; guard so tests can simulate drag events.
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (e.button !== 0) return;
    if (drawMode === "rectangle") {
      const grid = eventToGrid(e);
      rectStartRef.current = grid;
      setDraftPoints([grid, grid]);
      return;
    }
    // Polygon mode suppresses panning; vertices are placed on pointer-up.
    if (drawMode === "polygon") return;
    dragRef.current = {
      pointerId: e.pointerId,
      mode: "pan",
      start: { x: e.clientX, y: e.clientY },
      origin: view.offset,
      marker: null,
      originLayer: { x: 0, y: 0 },
    };
    // jsdom has no pointer capture; guard so tests can simulate drag events.
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    setCursor(viewportPoint(e));
    const drag = dragRef.current;
    if (drawMode === "rectangle" && rectStartRef.current) {
      setDraftPoints([rectStartRef.current, eventToGrid(e)]);
      return;
    }
    if (!drag || drag.pointerId !== e.pointerId) return;

    if (drag.mode === "pan") {
      setView((prev) => ({
        ...prev,
        offset: {
          x: drag.origin.x + (e.clientX - drag.start.x),
          y: drag.origin.y + (e.clientY - drag.start.y),
        },
      }));
      return;
    }

    if (!drag.marker) return;
    // Drag deltas are expressed in world-layer pixels so markers track the
    // cursor one-to-one at any zoom level.
    const dx = (e.clientX - drag.start.x) / view.zoom;
    const dy = (e.clientY - drag.start.y) / view.zoom;

    if (drag.mode === "move") {
      setDragPos({ x: drag.originLayer.x + dx, y: drag.originLayer.y + dy });
    } else {
      const viewport = viewportPoint(e);
      const pointerLayer = {
        x: viewport.x - view.offset.x,
        y: viewport.y - view.offset.y,
      };
      const radius = Math.abs(pointerLayer.x - drag.originLayer.x);
      setRingRange(clampAreaRange(radius / BASE_RING_GRID_UNITS));
    }
  }

  function handlePointerUp(e: React.PointerEvent<HTMLDivElement>) {
    // Zone drawing never runs while a marker drag owns the pointer.
    if (drawMode === "rectangle" && !dragRef.current) {
      const start = rectStartRef.current;
      rectStartRef.current = null;
      setDraftPoints(null);
      if (start) {
        const end = eventToGrid(e);
        if (end.x !== start.x && end.y !== start.y) {
          onZoneDrawn?.("rectangle", [start, end]);
        }
      }
      return;
    }
    if (drawMode === "polygon" && !dragRef.current) {
      // Compute the grid point outside the updater: React releases the event's
      // currentTarget before lazy state updater callbacks run.
      const grid = eventToGrid(e);
      setDraftPoints((prev) => [...(prev ?? []), grid]);
      return;
    }
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;

    if (drag.mode === "move" && drag.marker && dragPos) {
      onMoveMarker?.(
        drag.marker,
        Math.round(dragPos.x - MAP_PIXEL_SIZE / 2),
        Math.round(dragPos.y - MAP_PIXEL_SIZE / 2),
      );
    } else if (drag.mode === "ring" && drag.marker && ringRange !== null) {
      onAreaRangeChange?.(drag.marker, ringRange);
    }

    dragRef.current = null;
    setDragMarkerId(null);
    setDragPos(null);
    setRingRange(null);
  }

  function handleDoubleClick() {
    if (drawMode === "polygon" && draftPoints && draftPoints.length >= 3) {
      onZoneDrawn?.("polygon", draftPoints);
      setDraftPoints(null);
    }
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
        <span className="mx-1 h-5 w-px bg-shell-line" aria-hidden="true" />
        <button
          type="button"
          className={toolbarButton}
          onClick={() => toggleDraw("rectangle")}
          title="Draw rectangle exclusion zone"
          aria-label="Draw rectangle exclusion zone"
          aria-pressed={drawMode === "rectangle"}
        >
          <IconRect />
        </button>
        <button
          type="button"
          className={toolbarButton}
          onClick={() => toggleDraw("polygon")}
          title="Draw polygon exclusion zone"
          aria-label="Draw polygon exclusion zone"
          aria-pressed={drawMode === "polygon"}
        >
          <IconPolygon />
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
        className={[
          "relative min-h-0 flex-1 touch-none select-none overflow-hidden bg-shell-panel",
          drawMode === "none"
            ? "cursor-grab active:cursor-grabbing"
            : "cursor-crosshair",
        ].join(" ")}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={() => setCursor(null)}
        onDoubleClick={handleDoubleClick}
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
          {/* Persistent exclusion zones + the active drawing draft */}
          {zones.map((zone) => (
            <ZoneShapeSvg
              key={zone.id}
              corners={zone.points}
              draft={false}
              testId={`map-zone-${zone.id}`}
            />
          ))}
          {drawMode !== "none" && draftPoints && draftPoints.length > 0 && (
            <ZoneShapeSvg
              corners={
                drawMode === "rectangle" && draftPoints.length === 2
                  ? draftPoints
                  : cursorMap
                    ? [...draftPoints, cursorMap]
                    : draftPoints
              }
              draft
              testId="map-zone-draft"
            />
          )}
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
              {markers.map((marker) => {
                const pos = markerLayerPos(marker);
                const isDragging = dragMarkerId === marker.id;
                const areaRange =
                  isDragging && ringRange !== null
                    ? ringRange
                    : (marker.areaRange ?? null);
                const ringRadius =
                  areaRange !== null ? areaRange * BASE_RING_GRID_UNITS : null;
                return (
                  <div key={marker.id}>
                    {ringRadius !== null && (
                      <svg
                        className="pointer-events-none absolute text-shell-accent"
                        style={{
                          left: pos.x - ringRadius,
                          top: pos.y - ringRadius,
                          width: ringRadius * 2,
                          height: ringRadius * 2,
                          overflow: "visible",
                        }}
                        data-testid={`map-base-ring-${marker.id}`}
                        aria-hidden="true"
                      >
                        <circle
                          cx={ringRadius}
                          cy={ringRadius}
                          r={ringRadius}
                          fill="currentColor"
                          fillOpacity={0.08}
                          stroke="currentColor"
                          strokeWidth={1.5}
                          strokeDasharray="4 3"
                        />
                      </svg>
                    )}
                    <div
                      className={[
                        "absolute -translate-x-1/2 -translate-y-1/2 touch-none",
                        marker.markerType === "Base" ? "cursor-move" : "cursor-grab",
                        isDragging ? "z-10" : "",
                      ].join(" ")}
                      style={{ left: pos.x, top: pos.y }}
                      onPointerDown={(e) => beginMarkerDrag(e, marker, "move")}
                      onMouseEnter={() => setHoveredMarkerId(marker.id)}
                      onMouseLeave={() =>
                        setHoveredMarkerId((id) => (id === marker.id ? null : id))
                      }
                      data-testid={`map-marker-${marker.id}`}
                    >
                      <span
                        className={[
                          "block rounded-full border border-shell-line shadow-sm transition-transform",
                          marker.markerType === "Base"
                            ? "bg-shell-accent"
                            : "bg-shell-warning",
                          marker.markerType === "Base" ? "h-3 w-3" : "h-2.5 w-2.5",
                          isDragging ? "scale-125" : "",
                        ].join(" ")}
                      />
                    </div>
                    {ringRadius !== null && (
                      <div
                        className={[
                          "absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 touch-none rounded-full border border-shell-accent bg-shell-surface shadow-sm",
                          isDragging ? "z-10" : "",
                        ].join(" ")}
                        style={{ left: pos.x + ringRadius, top: pos.y }}
                        onPointerDown={(e) => beginMarkerDrag(e, marker, "ring")}
                        onMouseEnter={() => setHoveredMarkerId(marker.id)}
                        onMouseLeave={() =>
                          setHoveredMarkerId((id) => (id === marker.id ? null : id))
                        }
                        title="Drag to resize base area range"
                        data-testid={`map-ring-handle-${marker.id}`}
                      />
                    )}
                  </div>
                );
              })}
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

        {/* Hover overlay */}
        {hoveredMarkerId && !dragMarkerId && (
          <HoverOverlay
            marker={markers.find((m) => m.id === hoveredMarkerId) ?? null}
          />
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
        <span data-testid="map-status-right">
          {drawMode === "polygon" && draftPoints
            ? `${draftPoints.length} vertex(ies)`
            : `${markers.length} marker(s)`}
        </span>
      </div>
    </div>
  );
}
