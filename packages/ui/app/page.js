"use client";

import { useEffect, useState } from "react";

// NEXT_PUBLIC_API_URL is baked in when the UI is built (see packages/ui/Dockerfile)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [api, setApi] = useState("checking...");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((d) => setApi(d.status === "ok" ? "connected" : "unexpected reply"))
      .catch(() => setApi("not reachable"));
  }, []);

  return (
    <main>
      <h1>WebAwesome Scheduler</h1>
      <p>Job management for cleaning and pest-control businesses.</p>
      <p>
        API status: <strong>{api}</strong>
      </p>
      <p style={{ color: "#666" }}>This is the starting page. Screens for customers, jobs and quotes come next.</p>
    </main>
  );
}
