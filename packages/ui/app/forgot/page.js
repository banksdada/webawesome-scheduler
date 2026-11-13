"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "../lib/api";
import AuthShell from "../components/AuthShell";
import Icon from "../components/Icon";

export default function Forgot() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/auth/forgot", { method: "POST", body: { email } });
      setSent(true);
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  }

  return (
    <AuthShell>
      <form className="card" onSubmit={submit}>
        <h1>Forgot your password?</h1>
        {sent ? (
          <>
            <div className="ok">
              <Icon name="mail" size={18} /> If <strong>{email}</strong> has an account, we've sent an email with a link to choose a new password.
            </div>
            <p className="muted">The link works for one hour. If nothing arrives in a few minutes, check your spam folder.</p>
            <p><Link href="/login">Back to log in</Link></p>
          </>
        ) : (
          <>
            <p className="muted">Enter the email you log in with and we'll send you a link.</p>
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
            {error && <div className="error">{error}</div>}
            <p><button disabled={busy}>{busy ? "Sending..." : "Send me a link"}</button></p>
            <p className="muted"><Link href="/login">Back to log in</Link></p>
          </>
        )}
      </form>
    </AuthShell>
  );
}
