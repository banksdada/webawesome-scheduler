"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveSession } from "../lib/api";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api("/token", { method: "POST", form: { username: email, password } });
      saveSession({ token: data.access_token, role: data.role, name: data.name });
      router.push(data.role === "admin" ? "/schedule" : "/my-jobs");
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <form className="card narrow" onSubmit={submit}>
      <h1>Log in</h1>
      <label>Email</label>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
      <label>Password</label>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
      {error && <div className="error">{error}</div>}
      <p><button disabled={busy}>{busy ? "Logging in..." : "Log in"}</button></p>
      <p className="muted">New business? <Link href="/signup">Create an account</Link></p>
    </form>
  );
}
