// User-selectable look of the overlays, mirroring backend/app/video/style.py.
// To add a font: add it there, put the .ttf into src/assets/fonts/, add an @font-face in
// App.css and an entry here.
import type { CSSProperties } from "react";
import type { FontId, GlowLevel, OverlayDesign, VideoKind, VideoSettings } from "../types/analysis";

export const DEFAULT_OVERLAY_SCALE = 0.5;
export const DEFAULT_OVERLAY_DESIGN: OverlayDesign = {
  color: "#00e5ff",
  showGrid: true,
  spectrumStyle: "curve",
  showFrame: true,
  font: "orbitron",
  glow: "normal",
  scale: DEFAULT_OVERLAY_SCALE,
};

// scale: evens out the visual size between fonts, as FontSpec.scale in the backend.
export const FONTS: { id: FontId; label: string; family: string; hint: string; scale: number }[] = [
  { id: "orbitron", label: "Orbitron", family: '"Orbitron"', hint: "Neon-Tech", scale: 1 },
  { id: "montserrat", label: "Montserrat", family: '"Montserrat"', hint: "Modern, clean", scale: 1.05 },
  { id: "bebas", label: "Bebas Neue", family: '"Bebas Neue"', hint: "Bold, YouTube style", scale: 1.1 },
  { id: "playfair", label: "Playfair", family: '"Playfair Display"', hint: "Elegant, classic", scale: 1.1 },
  { id: "pixel", label: "Pixel", family: '"Press Start 2P"', hint: "Retro game", scale: 0.72 },
  { id: "handwriting", label: "Handwriting", family: '"Caveat"', hint: "Personal, handwritten", scale: 1.35 },
];

export const GLOW_LEVELS: { id: GlowLevel; label: string; factor: number }[] = [
  { id: "subtle", label: "Subtle", factor: 0.3 },
  { id: "normal", label: "Normal", factor: 1.0 },
];

export function fontFamily(id: FontId): string {
  return FONTS.find((f) => f.id === id)?.family ?? '"Orbitron"';
}

export function glowFactor(id: GlowLevel): number {
  return GLOW_LEVELS.find((g) => g.id === id)?.factor ?? 1;
}

export function overlayDesign(settings: Pick<VideoSettings, "designMode" | "globalDesign" | "featureDesigns">, kind: VideoKind): OverlayDesign {
  return settings.designMode === "global" ? settings.globalDesign : settings.featureDesigns[kind];
}

/** CSS variables the overlay styles read (App.css): font, its size factor and glow strength. */
export function overlayStyle(settings: Pick<OverlayDesign, "font" | "glow">): CSSProperties {
  return {
    "--overlay-font": fontFamily(settings.font),
    "--font-scale": FONTS.find((f) => f.id === settings.font)?.scale ?? 1,
    "--glow": glowFactor(settings.glow),
  } as CSSProperties;
}
