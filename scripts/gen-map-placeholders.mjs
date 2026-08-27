// Generates placeholder PNG map tiles for the phase 16 map canvas with zero
// dependencies. Tiles are 512x512 blocky rasters displayed at 2048x2048 so the
// canvas has real raster assets to render until authentic Palworld map tiles
// are bundled. Deterministic output: same seed, same bytes.
//
// Usage: node scripts/gen-map-placeholders.mjs
import { deflateSync } from "node:zlib";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const SIZE = 512;
const BLOCK = 8; // pixel size of one terrain block (sampled on the block grid)
const GRID_STEP = 64; // map grid lines, in tile pixels
const MAP_DIR = join("resources", "assets", "map");

// ── Minimal PNG encoder (RGBA, 8-bit, filter 0) ──────────────────────────────

const CRC_TABLE = new Uint32Array(256);
for (let n = 0; n < 256; n += 1) {
  let c = n;
  for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  CRC_TABLE[n] = c >>> 0;
}

function crc32(buf) {
  let c = 0xffffffff;
  for (const byte of buf) c = CRC_TABLE[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  out.write(type, 4, "ascii");
  data.copy(out, 8);
  out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
  return out;
}

function encodePng(width, height, rgba) {
  const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // color type: RGBA
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y += 1) {
    raw[y * (stride + 1)] = 0; // filter: none
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  }
  return Buffer.concat([
    signature,
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", deflateSync(raw, { level: 9 })),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

// ── Deterministic value noise ─────────────────────────────────────────────────

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function valueNoiseGrid(cells, seed) {
  const rand = mulberry32(seed);
  const values = new Float64Array(cells * cells);
  for (let i = 0; i < values.length; i += 1) values[i] = rand();
  return (cx, cy) => {
    // Bilinear sample of the cell grid with wrap-around edges.
    const x0 = ((Math.floor(cx) % cells) + cells) % cells;
    const y0 = ((Math.floor(cy) % cells) + cells) % cells;
    const x1 = (x0 + 1) % cells;
    const y1 = (y0 + 1) % cells;
    const fx = cx - Math.floor(cx);
    const fy = cy - Math.floor(cy);
    const top = values[y0 * cells + x0] * (1 - fx) + values[y0 * cells + x1] * fx;
    const bottom = values[y1 * cells + x0] * (1 - fx) + values[y1 * cells + x1] * fx;
    return top * (1 - fy) + bottom * fy;
  };
}

// ── World map placeholder: muted landmasses, water, and map grid ─────────────

const WATER_DEEP = [38, 52, 66];
const WATER_SHALLOW = [58, 78, 94];
const LAND_DARK = [62, 70, 56];
const LAND_MID = [84, 92, 70];
const LAND_LIGHT = [110, 114, 88];

function mix(a, b, t) {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t),
  ];
}

function generateWorldMap() {
  const rgba = Buffer.alloc(SIZE * SIZE * 4);

  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      // Constant color per BLOCK so scanlines compress well.
      const n = valueNoiseGrid(SIZE / BLOCK, 20260828)(
        Math.floor(x / BLOCK) / 6,
        Math.floor(y / BLOCK) / 6,
      );
      let rgb;
      if (n < 0.42) {
        rgb = mix(WATER_DEEP, WATER_SHALLOW, n / 0.42);
      } else {
        const t = (n - 0.42) / 0.58;
        rgb =
          t < 0.5
            ? mix(LAND_DARK, LAND_MID, t * 2)
            : mix(LAND_MID, LAND_LIGHT, (t - 0.5) * 2);
      }
      // Map grid lines every GRID_STEP pixels.
      if (x % GRID_STEP === 0 || y % GRID_STEP === 0) {
        rgb = mix(rgb, [232, 234, 237], 0.16);
      }
      const i = (y * SIZE + x) * 4;
      rgba[i] = rgb[0];
      rgba[i + 1] = rgb[1];
      rgba[i + 2] = rgb[2];
      rgba[i + 3] = 255;
    }
  }
  return encodePng(SIZE, SIZE, rgba);
}

// ── Treemap overlay: transparent biome and water blobs ───────────────────────

const FOREST = [44, 90, 44];
const WATER_TINT = [26, 92, 138];

function generateTreemapOverlay() {
  const blobs = [
    { x: 125, y: 125, r: 75, kind: "forest" },
    { x: 375, y: 125, r: 62, kind: "forest" },
    { x: 250, y: 300, r: 100, kind: "forest" },
    { x: 75, y: 375, r: 50, kind: "forest" },
    { x: 425, y: 400, r: 75, kind: "forest" },
    { x: 200, y: 450, r: 62, kind: "forest" },
    { x: 450, y: 75, r: 50, kind: "water" },
    { x: 50, y: 450, r: 45, kind: "water" },
  ];
  const rgba = Buffer.alloc(SIZE * SIZE * 4);

  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      for (const blob of blobs) {
        const dx = x - blob.x;
        const dy = y - blob.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < blob.r) {
          // Soft edge: alpha fades out over the outer 25% of the radius.
          const edge = Math.min(1, (blob.r - dist) / (blob.r * 0.25));
          const alpha = Math.round((blob.kind === "forest" ? 0.22 : 0.28) * edge * 255);
          const i = (y * SIZE + x) * 4;
          const tint = blob.kind === "forest" ? FOREST : WATER_TINT;
          rgba[i] = tint[0];
          rgba[i + 1] = tint[1];
          rgba[i + 2] = tint[2];
          rgba[i + 3] = alpha;
        }
      }
    }
  }
  return encodePng(SIZE, SIZE, rgba);
}

mkdirSync(MAP_DIR, { recursive: true });
const worldPng = generateWorldMap();
const treemapPng = generateTreemapOverlay();
writeFileSync(join(MAP_DIR, "world-map.png"), worldPng);
writeFileSync(join(MAP_DIR, "treemap-overlay.png"), treemapPng);
console.log(
  `Generated placeholder map tiles in ${MAP_DIR}: world-map.png (${worldPng.length} bytes), treemap-overlay.png (${treemapPng.length} bytes)`,
);
