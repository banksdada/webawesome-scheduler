"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { useSession } from "../lib/useSession";

const EMPTY = { name: "", email: "", phone: "", password: "" };

export default function Team() {
  const { ready } = useSession({ role: "admin" });
  const [list, setList] = useState([]);
  const [f, setF] = useState(EMPTY);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");
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

  if (!ready) return null;
  return (
    <>
      <h1>Team</h1>
      <form className="card" onSubmit={add}>
        <h2 style={{ marginTop: 0 }}>Add a technician</h2>
        <div className="grid2">
          <div><label>Name</label><input value={f.name} onChange={set("name")} required /></div>
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
                <td>{m.name}</td>
                <td>{m.email}</td>
                <td>{m.role}</td>
                <td><button className="secondary" onClick={() => toggle(m)}>{m.active ? "Deactivate" : "Reactivate"}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
