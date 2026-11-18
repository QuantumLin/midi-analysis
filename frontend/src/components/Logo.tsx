// Logo: the icon (piano keys rising like analyzer bars, public/logo.svg) and the wordmark
// in the overlays' display font. Works on the light and the dark theme.
export default function Logo() {
  return (
    <h1 className="logo">
      <img className="logo__icon" src="/logo.svg" alt="" width={40} height={40} />
      <span className="logo__word">
        <span className="logo__midi">MIDI</span>
        <span className="logo__analysis">Analysis</span>
      </span>
    </h1>
  );
}
