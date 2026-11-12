"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { useSession } from "../lib/useSession";

const EMPTY = { name: "", phone: "", email: "", address: "", notes: "" };

export default function Customers() {
  const { ready } = useSession({ role: "admin" });
  const [list, setList] = useState([]);
  const [f, setF] = useState(EMPTY);
  const [error, setError] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const load = useCallback(async () => {
    try {
      setList(await api("/customers"));
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
    try {
      await api("/customers", { method: "POST", body: f });
      setF(EMPTY);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!ready) return null;
  return (
    <>
      <h1>Customers</h1>
      <form className="card" onSubmit={add}>
        <div className="grid2">
          <div><label>Name</label><input value={f.name} onChange={set("name")} required /></div>
          <div><label>Phone</label><input value={f.phone} onChange={set("phone")} /></div>
          <div><label>Email</label><input value={f.email} onChange={set("email")} /></div>
          <div><label>Address</label><input value={f.address} onChange={set("address")} /></div>
        </div>
        <label>Notes (access, pets, parking...)</label>
        <textarea rows={2} value={f.notes} onChange={set("notes")} />
        {error && <div className="error">{error}</div>}
        <p><button>Add customer</button></p>
      </form>
      <div className="card">
        {list.length === 0 ? (
          <p className="muted">No customers yet.</p>
        ) : (
          <table>
            <thead><tr><th>Name</th><th>Phone</th><th>Address</th></tr></thead>
            <tbody>
              {list.map((c) => (
                <tr key={c.id}><td>{c.name}</td><td>{c.phone}</td><td>{c.address}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
