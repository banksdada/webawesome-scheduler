"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "../lib/api";
import AuthShell from "../components/AuthShell";
import Icon from "../components/Icon";

function ResetForm() {
  const token = useSearchParams().get("token") || "";
  const [password, setPassword] = useState("");
  const [again, setAgain] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (password !== again) {
      setError("The two passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      await api("/auth/reset", { method: "POST", body: { token, password } });
      setDone(true);
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  }

  if (!token) {
    return (
      <form className="card">
        <h1>Choose a new password</h1>
        <div className="warn">This page needs the link from your email. Open the link again, or ask for a new one.</div>
        <p><Link href="/forgot">Send me a new link</Link></p>
      </form>
    );
  }

  if (done) {
    return (
      <form className="card">
        <h1>Password changed</h1>
        <div className="ok"><Icon name="check" size={18} /> You can now log in with your new password.</div>
        <p><Link className="btn" href="/login">Log in</Link></p>
      </form>
    );
  }

  return (
    <form className="card" onSubmit={submit}>
      <h1>Choose a new password</h1>
      <label>New password (at least 8 characters)</label>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
      <label>Type it again</label>
      <input type="password" value={again} onChange={(e) => setAgain(e.target.value)} required minLength={8} autoComplete="new-password" />
      {error && (
        <div className="error">
          {error} {error.includes("expired") && <Link href="/forgot">Send me a new link</Link>}
        </div>
      )}
      <p><button disabled={busy}>{busy ? "Saving..." : "Save new password"}</button></p>
    </form>
  );
}

export default function Reset() {
  return (
    <AuthShell>
      <Suspense fallback={null}>
        <ResetForm />
      </Suspense>
    </AuthShell>
  );
}
