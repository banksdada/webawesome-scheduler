"use client";

import { useCallback, useEffect, useState } from "react";
import { api, getSession, saveSession } from "../lib/api";
import { useSession } from "../lib/useSession";

const EMPTY = { name: "", email: "", phone: "", password: "" };

export default function Team() {
  const { ready } = useSession({ role: "admin" });
  const [list, setList] = useState([]);
  const [f, setF] = useState(EMPTY);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");
  const [editing, setEditing] = useState(null); // { id, name }
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = useCallback(async () => {
    try {
      setList(await api("/team"));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function add(e) {
    e.preventDefault();
    setError("");
    setDone("");
    try {
      await api("/team", { method: "POST", body: f });
      setDone(`${f.name} can now log in with ${f.email} and the password you set.`);
      setF(EMPTY);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggle(member) {
    setError("");
    try {
      await api(`/team/${member.id}`, { method: "PATCH", body: { active: !member.active } });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function rename(e) {
    e.preventDefault();
    const name = editing.name.trim();
    if (!name) return;
    setError("");
    try {
      const updated = await api(`/team/${editing.id}`, { method: "PATCH", body: { name } });
      const me = getSession();
      // If you renamed yourself, the greeting in the menu changes straight away.
      if (me && me.name && list.find((m) => m.id === editing.id)?.name === me.name) saveSession({ ...me, name: updated.name });
      setEditing(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!ready) return null;
  return (
    <>
      <h1>Team</h1>
      <form className="card" onSubmit={add}>
        <h2 style={{ marginTop: 0 }}>Add a technician</h2>
        <div className="grid2">
          <div><label>Name</label><input value={f.name} onChange={set("name")} placeholder="For example, Sam Rivera" required /><p className="muted hint">Use their real name. It's how the app greets them.</p></div>
          <div><label>Phone</label><input value={f.phone} onChange={set("phone")} /></div>
          <div><label>Email (their login)</label><input type="email" value={f.email} onChange={set("email")} required /></div>
          <div><label>Password (at least 8 characters)</label><input type="text" value={f.password} onChange={set("password")} required minLength={8} /></div>
        </div>
        {error && <div className="error">{error}</div>}
        {done && <div className="ok">{done}</div>}
        <p><button>Add technician</button></p>
      </form>
      <div className="card">
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr></thead>
          <tbody>
            {list.map((m) => (
              <tr key={m.id} style={{ opacity: m.active ? 1 : 0.5 }}>
                <td>
                  {editing?.id === m.id ? (
                    <form className="row" onSubmit={rename}>
                      <input autoFocus value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} required />
                      <button>Save</button>
                      <button type="button" className="secondary" onClick={() => setEditing(null)}>Cancel</button>
                    </form>
                  ) : m.name}
                </td>
                <td>{m.email}</td>
                <td>{m.role}</td>
                <td>
                  <div className="row">
                    <button className="secondary" onClick={() => setEditing({ id: m.id, name: m.name })}>Rename</button>
                    <button className="secondary" onClick={() => toggle(m)}>{m.active ? "Deactivate" : "Reactivate"}</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
