"""Degree overlay: "STUFE" + the current chord as roman numeral (e.g. "vi"), below it the
last four numerals as a chain ("I – V – vi – IV", newest brightest) and the key they refer
to ("IN C-DUR"); the chain shows bare degrees, the big numeral the full chord ("V" with a raised "7"). When a known progression completes, its name replaces the key line in
full neon ("DIE POP-FORMEL ×2") and the panel glows brighter for a few seconds."""

from app.analysis.harmony import HarmonyAnalysis, split_numeral
from app.video.labels import Language, key_context, progression_text, text
from app.video.neon import Color, add_neon, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, VALUE_WEIGHT, NeonOverlay, flash_strength

PROGRESSION_GLOW = 1.8
CHAIN_LENGTH = 4
CHAIN_SEPARATOR = "  –  "
CHAIN_WEIGHT = 700
FOOTER_TRACKING = LABEL_TRACKING * 0.6
# Roman numerals need some air: Orbitron's "III" would otherwise read like a barcode.
NUMERAL_TRACKING = 0.08
SUFFIX_SCALE = 0.45  # "maj7", "°" ... set small and raised next to the big numeral
SUFFIX_WEIGHT = 700
CHAIN_TRACKING = 0.14


class HarmonyRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, harmony: HarmonyAnalysis):
        self.language = language
        self.harmony = harmony
        probe = NeonOverlay(width, height, color, 0, 0)
        self.value_size = probe.value_size
        self.suffix_size = max(8, round(probe.value_size * SUFFIX_SCALE))
        self.chain_size = max(8, round(46 * probe.u))
        self.chain_gap = 30 * probe.u
        self.footer_gap = 30 * probe.u
        self.small_size = probe.small_size

        chains = {harmony.chain_before(i, CHAIN_LENGTH) for i in range(len(harmony.chords))}
        footers = [key_context(k, language) for k in set(harmony.keys) if k]
        footers += [progression_text(h.id, h.count, language) for h in harmony.progressions]
        content_width = max(
            max((self._numeral_width(n) for n in harmony.numerals), default=0),
            max((self._chain_width(c) for c in chains), default=0),
            max((self._footer_width(f) for f in footers), default=0),
            probe.label_width(text("degree", language)),
            420 * probe.u,
        )
        content_height = probe.header_height + self.chain_gap + self.chain_size * 0.78 + self.footer_gap + probe.small_size
        super().__init__(width, height, color, content_width, content_height)

    def _numeral_width(self, numeral: str) -> float:
        degree, suffix = split_numeral(numeral)
        width = text_width(degree, self.value_size, VALUE_WEIGHT, NUMERAL_TRACKING)
        if suffix:
            width += self.suffix_size * 0.15 + text_width(suffix, self.suffix_size, SUFFIX_WEIGHT)
        return width

    def _chain_width(self, chain: tuple[str, ...]) -> float:
        return sum(text_width(p, self.chain_size, CHAIN_WEIGHT, CHAIN_TRACKING) for p, _ in _chain_pieces(chain))

    def _footer_width(self, footer: str) -> float:
        return text_width(footer.upper(), self.small_size, LABEL_WEIGHT, FOOTER_TRACKING)

    def state(self, chord_index: int | None, time: float):
        """chord_index: the chord shown at `time` (see render.chord_at), None = hidden."""
        if chord_index is None:
            return None
        harmony = self.harmony
        chord = harmony.chords[chord_index]
        strength = flash_strength(time - chord.start)
        hit = harmony.progression_at(time)
        key = harmony.keys[chord_index]
        if hit:
            footer = progression_text(hit.id, hit.count, self.language)
            strength = max(flash_strength(time - hit.time), PROGRESSION_GLOW)
        else:
            footer = key_context(key, self.language) if key else ""
        chain = harmony.chain_before(chord_index, CHAIN_LENGTH)
        return (harmony.numerals[chord_index], chain, footer, hit is not None, strength)

    def draw(self, state):
        numeral, chain, footer, highlighted, strength = state
        canvas = self.new_canvas()
        value_baseline = self.draw_header(canvas, text("degree", self.language), None, strength)
        degree, suffix = split_numeral(numeral)
        degree_width = text_width(degree, self.value_size, VALUE_WEIGHT, NUMERAL_TRACKING)
        x = self.center_x - self._numeral_width(numeral) / 2
        mask = self.new_mask()
        draw_text(mask, x + degree_width / 2, value_baseline, degree, self.value_size, VALUE_WEIGHT, NUMERAL_TRACKING)
        if suffix:
            suffix_width = text_width(suffix, self.suffix_size, SUFFIX_WEIGHT)
            suffix_x = x + degree_width + self.suffix_size * 0.15 + suffix_width / 2
            draw_text(mask, suffix_x, value_baseline - self.value_size * 0.36, suffix, self.suffix_size, SUFFIX_WEIGHT)
        add_neon(canvas, mask, self.color, radius=self.value_size * 0.22, strength=strength)

        # Chain: earlier numerals dim, the current one (last) bright.
        chain_baseline = value_baseline + self.chain_gap + self.chain_size * 0.78
        x = self.center_x - self._chain_width(chain) / 2
        dim, bright = self.new_mask(), self.new_mask()
        for piece, current in _chain_pieces(chain):
            w = text_width(piece, self.chain_size, CHAIN_WEIGHT, CHAIN_TRACKING)
            draw_text(bright if current else dim, x + w / 2, chain_baseline, piece, self.chain_size, CHAIN_WEIGHT,
                      CHAIN_TRACKING)  # fmt: skip
            x += w
        add_neon(canvas, dim, self.color, radius=self.chain_size * 0.3, strength=0.3, core_alpha=0.55)
        add_neon(canvas, bright, self.color, radius=self.chain_size * 0.3, strength=1.0)

        footer_baseline = chain_baseline + self.footer_gap + self.small_size * 0.8
        mask = self.new_mask()
        draw_text(mask, self.center_x, footer_baseline, footer.upper(), self.small_size, LABEL_WEIGHT, FOOTER_TRACKING)
        if highlighted:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=strength)
        else:
            add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=0.3, core_alpha=0.75)
        return canvas


def _chain_pieces(chain: tuple[str, ...]) -> list[tuple[str, bool]]:
    """Numerals and separators; True marks the current (last) numeral."""
    pieces: list[tuple[str, bool]] = []
    for k, item in enumerate(chain):
        if k:
            pieces.append((CHAIN_SEPARATOR, False))
        pieces.append((item, k == len(chain) - 1))
    return pieces
