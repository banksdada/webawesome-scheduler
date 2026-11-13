"use client";

import { useCallback, useEffect, useState } from "react";
import {
  addDays, api, fromLocalInput, sameDay, startOfDay, startOfWeek, timeOf, toLocalInput,
} from "../lib/api";
import { useSession } from "../lib/useSession";
import Icon from "../components/Icon";
import Spot from "../components/Spot";
import { toneFor } from "../lib/tones";

const EMPTY_JOB = { customer_id: "", title: "", notes: "", when: "", duration_minutes: 60, assigned_to_id: "", price_estimate: "" };

// A small form used for both "new job" and "edit job".
function JobForm({ customers, techs, initial, onSave, onCancel, onCancelJob, onQuote, saving, clash, error, isEdit }) {
  const [f, setF] = useState(initial);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function submit(e, allowOverlap = false) {
    e.preventDefault();
    onSave(f, allowOverlap);
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2 style={{ marginTop: 0 }}>{isEdit ? "Edit job" : "New job"}</h2>
      <div className="grid2">
        <div>
          <label>Customer</label>
          <select value={f.customer_id} onChange={set("customer_id")} required disabled={isEdit}>
            <option value="">Choose...</option>
            {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label>What needs doing</label>
          <input value={f.title} onChange={set("title")} required />
        </div>
        <div>
          <label>Date and time</label>
          <input type="datetime-local" value={f.when} onChange={set("when")} />
        </div>
        <div>
          <label>Length (minutes)</label>
          <input type="number" min={5} step={5} value={f.duration_minutes} onChange={set("duration_minutes")} />
        </div>
        <div>
          <label>Technician</label>
          <select value={f.assigned_to_id} onChange={set("assigned_to_id")}>
            <option value="">Unassigned</option>
            {techs.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>
        <div>
          <label>Notes for the technician</label>
          <input value={f.notes} onChange={set("notes")} />
        </div>
        <div>
          <label>Price estimate (£)</label>
          <input type="number" min={0} step="0.01" value={f.price_estimate} onChange={set("price_estimate")} />
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {clash && (
        <div className="warn">
          <strong>{clash.message}.</strong> Clashes with:{" "}
          {clash.conflicts.map((c) => `${c.title} (${timeOf(c.scheduled_start)})`).join(", ")}
          <div style={{ marginTop: ".5rem" }}>
            <button type="button" className="secondary" disabled={saving} onClick={(e) => submit(e, true)}>Save anyway</button>
          </div>
        </div>
      )}
      <div className="row" style={{ marginTop: ".75rem" }}>
        <button disabled={saving}>{saving ? "Saving..." : isEdit ? "Save changes" : "Create job"}</button>
        <button type="button" className="secondary" onClick={onCancel}>Close</button>
        {isEdit && <button type="button" className="secondary" onClick={onQuote}>View quote</button>}
        {isEdit && <button type="button" className="danger" onClick={onCancelJob}>Cancel this job</button>}
      </div>
    </form>
  );
}

export default function Schedule() {
  const { ready, session } = useSession({ role: "admin" });
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [techFilter, setTechFilter] = useState("");
  const [jobs, setJobs] = useState([]);
  const [unscheduled, setUnscheduled] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [team, setTeam] = useState([]);
  const [panel, setPanel] = useState(null); // null | {job?: existing job}
  const [saving, setSaving] = useState(false);
  const [clash, setClash] = useState(null);
  const [formError, setFormError] = useState("");
  const [error, setError] = useState("");

  const techs = team.filter((m) => m.active);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        start: weekStart.toISOString(),
        end: addDays(weekStart, 7).toISOString(),
      });
      if (techFilter) params.set("assigned_to_id", techFilter);
      const [week, todo] = await Promise.all([api(`/jobs?${params}`), api("/jobs?unscheduled=true")]);
      setJobs(week);
      setUnscheduled(todo);
    } catch (e) {
      setError(e.message);
    }
  }, [weekStart, techFilter]);

  useEffect(() => {
    if (!ready) return;
    Promise.all([api("/customers"), api("/team")])
      .then(([c, t]) => {
        setCustomers(c);
        setTeam(t);
      })
      .catch((e) => setError(e.message));
  }, [ready]);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  function openPanel(job) {
    setClash(null);
    setFormError("");
    setPanel({ job: job || null, key: Math.random() });
  }

  async function save(f, allowOverlap) {
    setSaving(true);
    setClash(null);
    setFormError("");
    const body = {
      title: f.title,
      notes: f.notes || null,
      scheduled_start: fromLocalInput(f.when),
      duration_minutes: Number(f.duration_minutes) || 60,
      assigned_to_id: f.assigned_to_id ? Number(f.assigned_to_id) : null,
      price_estimate: f.price_estimate === "" ? null : Number(f.price_estimate),
      allow_overlap: allowOverlap,
    };
    try {
      if (panel.job) {
        await api(`/jobs/${panel.job.id}`, { method: "PATCH", body });
      } else {
        await api("/jobs", { method: "POST", body: { ...body, customer_id: Number(f.customer_id) } });
      }
      setPanel(null);
      await load();
    } catch (err) {
      if (err.status === 409 && err.detail?.conflicts) setClash(err.detail);
      else setFormError(err.message);
    }
    setSaving(false);
  }

  async function cancelJob() {
    if (!window.confirm("Cancel this job?")) return;
    try {
      await api(`/jobs/${panel.job.id}`, { method: "PATCH", body: { status: "cancelled" } });
      setPanel(null);
      await load();
    } catch (err) {
      setFormError(err.message);
    }
  }

  async function viewQuote() {
    try {
      const q = await api(`/quotes/generate?job_id=${panel.job.id}`, { method: "POST" });
      const url = URL.createObjectURL(new Blob([q.html], { type: "text/html" }));
      window.open(url, "_blank");
    } catch (err) {
      setFormError(err.message);
    }
  }

  if (!ready) return null;

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  const today = new Date();
  const initial = panel?.job
    ? {
        customer_id: panel.job.customer.id,
        title: panel.job.title,
        notes: panel.job.notes || "",
        when: toLocalInput(panel.job.scheduled_start),
        duration_minutes: panel.job.duration_minutes,
        assigned_to_id: panel.job.assigned_to?.id || "",
        price_estimate: panel.job.price_estimate ?? "",
      }
    : EMPTY_JOB;

  const live = jobs.filter((j) => j.status !== "cancelled");
  const doneCount = live.filter((j) => j.status === "done").length;
  const estimate = live.reduce((sum, j) => sum + (Number(j.price_estimate) || 0), 0);
  const perDay = days.map((d) => live.filter((j) => j.scheduled_start && sameDay(new Date(j.scheduled_start), d)).length);
  const busiest = Math.max(1, ...perDay);

  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const firstName = session?.name ? session.name.split(" ")[0] : "";
  const todayJobs = live.filter((j) => j.scheduled_start && sameDay(new Date(j.scheduled_start), today));
  const todayDone = todayJobs.filter((j) => j.status === "done").length;
  const dayLine =
    todayJobs.length === 0
      ? "Nothing booked for today. A good moment to plan the week."
      : todayDone === todayJobs.length
        ? `All ${todayJobs.length} of today's jobs are done. Nice work, team.`
        : `${todayJobs.length} ${todayJobs.length === 1 ? "job" : "jobs"} today, ${todayDone} done so far.`;

  const initials = (n) => n.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  const card = (j) => (
    <div key={j.id} className={`job ${j.status}`} onClick={() => openPanel(j)}>
      <div className="time">{j.scheduled_start ? timeOf(j.scheduled_start) : "No time"}</div>
      <div className="title">{j.title}</div>
      <div className="cust">{j.customer.name}</div>
      <div className="foot">
        <span className={`avatar ${j.assigned_to ? `tone-${toneFor(j.assigned_to.name)}` : "none"}`}>{j.assigned_to ? initials(j.assigned_to.name) : "?"}</span>
        <span>{j.assigned_to ? j.assigned_to.name : "Unassigned"}</span>
        {j.status !== "assigned" && <span className={`badge ${j.status}`}>{j.status.replace("_", " ")}</span>}
      </div>
    </div>
  );

  const rangeLabel = `${weekStart.toLocaleDateString("en-GB", { day: "numeric", month: "short" })} – ${addDays(weekStart, 6).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}`;

  return (
    <>
      <section className="band">
        <div className="band-copy">
          <span className="band-range">{rangeLabel}</span>
          <h1>{greet}{firstName ? `, ${firstName}` : ""}</h1>
          <p>{dayLine}</p>
        </div>
        <Spot kind="rest" className="spot-band" />
      </section>
      {error && <div className="error">{error}</div>}
      <div className="stats">
        <div className="stat"><span className="ico spruce"><Icon name="calendar" /></span><div><b>{live.length}</b><span>jobs this week</span></div></div>
        <div className="stat"><span className="ico moss"><Icon name="check" /></span><div><b>{doneCount}</b><span>done</span></div></div>
        <div className="stat"><span className="ico signal"><Icon name="inbox" /></span><div><b>{unscheduled.length}</b><span>need a time</span></div></div>
        <div className="stat"><span className="ico blue"><Icon name="pound" /></span><div><b>£{estimate.toLocaleString("en-GB", { maximumFractionDigits: 0 })}</b><span>estimated value</span></div></div>
        <div className="stat bars">
          <div className="barchart" role="img" aria-label={`Jobs per day this week: ${perDay.join(", ")}`}>
            {perDay.map((n, i) => (
              <span key={i} className={sameDay(days[i], today) ? "on" : ""} style={{ height: `${Math.max(8, (n / busiest) * 100)}%` }} title={`${days[i].toLocaleDateString("en-GB", { weekday: "short" })}: ${n}`} />
            ))}
          </div>
          <span className="cap">jobs per day</span>
        </div>
      </div>
      <div className="toolbar">
        <button className="secondary" onClick={() => setWeekStart(addDays(weekStart, -7))}>Previous</button>
        <button className="secondary" onClick={() => setWeekStart(startOfWeek(new Date()))}>This week</button>
        <button className="secondary" onClick={() => setWeekStart(addDays(weekStart, 7))}>Next</button>
        <select style={{ width: "auto" }} value={techFilter} onChange={(e) => setTechFilter(e.target.value)}>
          <option value="">Everyone</option>
          {techs.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <button className="spacer" onClick={() => openPanel(null)} disabled={customers.length === 0}>New job</button>
      </div>
      {customers.length === 0 && <div className="warn">Add a customer first (Customers page), then you can create jobs.</div>}

      {panel && (
        <JobForm
          key={panel.key}
          customers={customers}
          techs={techs}
          initial={initial}
          isEdit={!!panel.job}
          saving={saving}
          clash={clash}
          error={formError}
          onSave={save}
          onCancel={() => setPanel(null)}
          onCancelJob={cancelJob}
          onQuote={viewQuote}
        />
      )}

      <div className="week">
        {days.map((d) => {
          const todays = jobs.filter((j) => j.scheduled_start && sameDay(new Date(j.scheduled_start), d));
          return (
            <div key={d.toISOString()} className={`day ${sameDay(d, today) ? "today" : ""}`}>
              <div className="dayhead">
                <span className="dow">{d.toLocaleDateString("en-GB", { weekday: "short" })}</span>
                <span className="num">{d.getDate()}</span>
                <span className="mon">{d.toLocaleDateString("en-GB", { month: "short" })}</span>
              </div>
              {todays.length === 0 ? <div className="empty">Free day</div> : todays.map(card)}
            </div>
          );
        })}
      </div>

      <h2>Needs a time</h2>
      {unscheduled.length === 0 ? <p className="muted emptynote"><Icon name="check" size={18} /> Every job has a time.</p> : <div className="week" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>{unscheduled.map(card)}</div>}
    </>
  );
}
