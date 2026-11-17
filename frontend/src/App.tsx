import { useEffect, useState } from "react";
import { fetchHealth } from "./api/client";

type BackendState = "checking" | "online" | "offline";

export default function App() {
  const [backend, setBackend] = useState<BackendState>("checking");

  useEffect(() => {
    fetchHealth()
      .then((health) => setBackend(health.status === "ok" ? "online" : "offline"))
      .catch(() => setBackend("offline"));
  }, []);

  return (
    <main className="app">
      <h1>MIDI Analytics</h1>
      <p className={`status status--${backend}`}>Backend: {backend}</p>
    </main>
  );
}
