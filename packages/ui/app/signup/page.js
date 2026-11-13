"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveSession } from "../lib/api";
import AuthShell from "../components/AuthShell";

export default function Signup() {
  const router = useRouter();
  const [f, setF] = useState({ organisation_name: "", name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api("/auth/signup", { method: "POST", body: f });
      saveSession({ token: data.access_token, role: data.role, name: data.name, platform_admin: !!data.platform_admin });
      router.push("/schedule");
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <AuthShell>
    <form className="card" onSubmit={submit}>
      <h1>Create your account</h1>
      <label>Business name</label>
      <input value={f.organisation_name} onChange={set("organisation_name")} required />
      <label>Your name</label>
      <input value={f.name} onChange={set("name")} required />
      <label>Email</label>
      <input type="email" value={f.email} onChange={set("email")} required autoComplete="email" />
      <label>Password (at least 8 characters)</label>
      <input type="password" value={f.password} onChange={set("password")} required minLength={8} autoComplete="new-password" />
      {error && <div className="error">{error}</div>}
      <p><button disabled={busy}>{busy ? "Creating..." : "Create account"}</button></p>
      <p className="muted">Already have an account? <Link href="/login">Log in</Link></p>
    </form>
    </AuthShell>
  );
}
