/** 83.4 -> "1:23.4" */
export function formatTime(seconds: number, decimals = 1): string {
  const minutes = Math.floor(seconds / 60);
  const width = decimals ? 3 + decimals : 2; // "05.3" / "05"
  const rest = (seconds - minutes * 60).toFixed(decimals).padStart(width, "0");
  return `${minutes}:${rest}`;
}
