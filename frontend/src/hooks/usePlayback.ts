import { useEffect, useState } from "react";

/** A play/pause clock over [0, duration] driven by requestAnimationFrame. */
export function usePlayback(duration: number) {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;
    const startedAt = performance.now() - time * 1000;
    let frame = requestAnimationFrame(function tick(now) {
      const t = (now - startedAt) / 1000;
      if (t >= duration) {
        setTime(duration);
        setPlaying(false);
        return;
      }
      setTime(t);
      frame = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(frame);
    // `time` is deliberately not a dependency: it is read once when playback starts,
    // otherwise the clock would restart on every frame.
  }, [playing, duration]);

  // A new piece starts from the beginning.
  useEffect(() => {
    setPlaying(false);
    setTime(0);
  }, [duration]);

  return {
    time,
    playing,
    toggle() {
      if (!playing && time >= duration) setTime(0);
      setPlaying((p) => !p);
    },
    seek(t: number) {
      setPlaying(false);
      setTime(Math.min(Math.max(t, 0), duration));
    },
  };
}
