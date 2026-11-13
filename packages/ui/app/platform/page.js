"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";
import { useSession } from "../lib/useSession";

// Owner-only. The API enforces this too: anyone else gets "Platform admins only".
export default function Platform() {
  const router = useRouter();
  const { session, ready } = useSession();
  const [orgs, setOrgs] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      setOrgs(await api("/platform/orgs"));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (!session?.platform_admin) {
      router.replace("/");
      return;
    }
    load();
  }, [ready, session, router, load]);

  async function toggle(org) {
    const verb = org.suspended ? "reactivate" : "suspend";
    const sure = org.suspended
      ? `Reactivate ${org.name}? Everyone in this business will be able to log in again.`
      : `Suspend ${org.name}? Everyone in this business will be locked out until you reactivate it.`;
    if (!window.confirm(sure)) return;
    setBusyId(org.id);
    setError("");
    try {
      await api(`/platform/orgs/${org.id}/${verb}`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e.message);
    }
    setBusyId(null);
  }

  if (!ready || !session?.platform_admin) return null;

  return (
    <>
      <div className="pagehead">
        <h1>Businesses</h1>
        {orgs && <span className="range">{orgs.length} signed up</span>}
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {orgs === null ? (
          <p className="muted">Loading...</p>
        ) : orgs.length === 0 ? (
          <p className="muted">No businesses yet.</p>
        ) : (
          <table>
            <thead>
              <tr><th>Business</th><th>Joined</th><th>People</th><th>Customers</th><th>Jobs</th><th>Status</th><th /></tr>
            </thead>
            <tbody>
              {orgs.map((o) => (
                <tr key={o.id}>
                  <td><strong>{o.name}</strong></td>
                  <td>{new Date(o.created_at + "Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</td>
                  <td>{o.users}</td>
                  <td>{o.customers}</td>
                  <td>{o.jobs}</td>
                  <td>{o.suspended ? <span className="badge cancelled">Suspended</span> : <span className="badge done">Active</span>}</td>
                  <td>
                    <button className={o.suspended ? "secondary" : "danger"} disabled={busyId === o.id} onClick={() => toggle(o)}>
                      {o.suspended ? "Reactivate" : "Suspend"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
