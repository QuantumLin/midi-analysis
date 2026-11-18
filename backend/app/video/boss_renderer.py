"""Boss fight overlay, in three phases:

- warning  (WARNING_SECONDS before the passage): "ACHTUNG: BOSS NAHT!" blinking, full HP bar
- fight    "ENDGEGNER" + the boss's name, an HP bar that drops with every note, "HP 63 %"
- defeated (DEFEATED_SECONDS after the passage): "BESIEGT!" in bright neon, empty bar

Outside these phases the frame is empty.
"""

from PIL import ImageDraw

from app.analysis.boss_fight import BossFight
from app.video.labels import BOSS_NAMES, Language, decimal, text
from app.video.neon import Color, add_neon, draw_text, text_width
from app.video.neon_overlay import LABEL_TRACKING, LABEL_WEIGHT, NeonOverlay, flash_strength

WARNING_SECONDS = 3.0
DEFEATED_SECONDS = 3.0
BLINK_SECONDS = 0.5
HP_SEGMENTS = 30
HP_STEPS = 100  # health is shown in whole percent
DEFEATED_GLOW = 2.0
UNLIT_ALPHA = 0.16
FOOTER_TRACKING = LABEL_TRACKING * 0.6


class BossRenderer(NeonOverlay):
    def __init__(self, width: int, height: int, color: Color, language: Language, boss: BossFight | None):
        self.language = language
        self.boss = boss
        probe = NeonOverlay(width, height, color, 0, 0)
        self.bar_gap = 26 * probe.u
        self.bar_height = 22 * probe.u
        self.footer_gap = 30 * probe.u
        name = BOSS_NAMES[boss.factor][language] if boss else ""
        footers = [text("boss_warning", language), self._details(100)]
        content_width = max(
            probe.value_width(name),
            probe.value_width(text("defeated", language)),
            max(text_width(f.upper(), probe.small_size, LABEL_WEIGHT, FOOTER_TRACKING) for f in footers),
            probe.label_width(text("final_boss", language)),
            520 * probe.u,
        )
        content_height = probe.header_height + self.bar_gap + self.bar_height + self.footer_gap + probe.small_size
        super().__init__(width, height, color, content_width, content_height)
        self.content_width = content_width

    def _details(self, health_percent: int) -> str:
        difficulty = decimal(self.boss.difficulty, self.language) if self.boss else "0"
        return f"{text('health', self.language)} {health_percent} %  ·  {text('difficulty', self.language)} {difficulty}/10"

    def state(self, time: float):
        """(phase, health in percent, glow strength, warning lit) or None."""
        boss = self.boss
        if boss is None:
            return None
        if boss.start - WARNING_SECONDS <= time < boss.start:
            lit = int((time - boss.start) // BLINK_SECONDS) % 2 == 0
            return ("warning", 100, 1.6 if lit else 1.0, lit)
        if boss.start <= time < boss.end:
            health = round(boss.health_at(time) * HP_STEPS)
            return ("fight", health, flash_strength(time - boss.start), True)
        if boss.end <= time < boss.end + DEFEATED_SECONDS:
            return ("defeated", 0, max(flash_strength(time - boss.end), DEFEATED_GLOW), True)
        return None

    def render(self, time: float) -> bytes:
        return self.render_state(self.state(time))

    def draw(self, state):
        phase, health, strength, lit = state
        canvas = self.new_canvas()
        name = BOSS_NAMES[self.boss.factor][self.language]
        value = text("defeated", self.language) if phase == "defeated" else name
        value_baseline = self.draw_header(canvas, text("final_boss", self.language), value, strength,
                                          label_accent=phase != "fight")  # fmt: skip

        # HP bar: lit segments for the remaining health.
        bar_top = value_baseline + self.bar_gap
        lit_segments = round(health / HP_STEPS * HP_SEGMENTS)
        segment_width = self.content_width / HP_SEGMENTS
        lit_mask, unlit_mask = self.new_mask(), self.new_mask()
        for i in range(HP_SEGMENTS):
            x0 = self.left + i * segment_width + segment_width * 0.1
            x1 = self.left + (i + 1) * segment_width - segment_width * 0.1
            ImageDraw.Draw(lit_mask if i < lit_segments else unlit_mask).rounded_rectangle(
                [(x0, bar_top), (x1, bar_top + self.bar_height)], radius=self.bar_height * 0.25, fill=255
            )
        add_neon(canvas, unlit_mask, self.color, radius=1, strength=0, core_alpha=UNLIT_ALPHA)
        add_neon(canvas, lit_mask, self.color, radius=self.bar_height * 0.8, strength=min(strength, 1.6))

        footer = text("boss_warning", self.language) if phase == "warning" else self._details(health)
        mask = self.new_mask()
        baseline = bar_top + self.bar_height + self.footer_gap + self.small_size * 0.8
        draw_text(mask, self.center_x, baseline, footer.upper(), self.small_size, LABEL_WEIGHT, FOOTER_TRACKING)
        accent = phase == "warning" and lit
        add_neon(canvas, mask, self.color, radius=self.small_size * 0.5, strength=strength if accent else 0.3,
                 core_alpha=1.0 if accent else 0.75)  # fmt: skip
        return canvas
