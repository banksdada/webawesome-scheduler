"use client";

import { useCallback, useEffect, useState } from "react";
import { addDays, api, dayLabel, sameDay, startOfDay, timeOf } from "../lib/api";
import { useSession } from "../lib/useSession";

function JobCard({ job, onAction, busy }) {
  const maps = job.customer.address
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(job.customer.address)}`
    : null;
  return (
    <div className={`jobcard ${job.status}`}>
      <div className="when">
        <span className="t">{job.scheduled_start ? timeOf(job.scheduled_start) : "No time"}</span>
        <span className="d">
          {job.scheduled_start ? dayLabel(new Date(job.scheduled_start)) : ""} · {job.duration_minutes} min
        </span>
        {job.status !== "assigned" && <span className={`badge ${job.status}`}>{job.status.replace("_", " ")}</span>}
      </div>
      <h3>{job.title}</h3>
      <div><strong>{job.customer.name}</strong></div>
      {job.customer.address && <div className="addr">{job.customer.address}</div>}
      {(job.customer.phone || maps) && (
        <div className="actions">
          {job.customer.phone ? <a href={`tel:${job.customer.phone}`}>Call</a> : <span />}
          {maps ? <a href={maps} target="_blank" rel="noreferrer">Directions</a> : <span />}
        </div>
      )}
      {job.notes && <div className="note">{job.notes}</div>}
      {job.status === "assigned" && (
        <button className="big" disabled={busy} onClick={() => onAction(job, "start")}>Start job</button>
      )}
      {job.status === "in_progress" && (
        <button className="big finish" disabled={busy} onClick={() => onAction(job, "complete")}>Mark as done</button>
      )}
    </div>
  );
}

export default function MyJobs() {
  const { ready } = useSession();
  const [jobs, setJobs] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const today = startOfDay(new Date());
      const params = new URLSearchParams({
        start: addDays(today, -7).toISOString(),
        end: addDays(today, 30).toISOString(),
      });
      setJobs(await api(`/jobs?${params}`));
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  async function act(job, action) {
    setBusy(true);
    setError("");
    try {
      await api(`/jobs/${job.id}/${action}`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e.message);
    }
    setBusy(false);
  }

  if (!ready || jobs === null) return <p className="muted">{error || "Loading..."}</p>;

  const today = new Date();
  const mine = jobs.filter((j) => j.status !== "cancelled");
  const open = (j) => j.status === "assigned" || j.status === "in_progress";
  const todays = mine.filter((j) => j.scheduled_start && sameDay(new Date(j.scheduled_start), today));
  const upcoming = mine.filter((j) => open(j) && new Date(j.scheduled_start) >= startOfDay(addDays(today, 1)));
  const overdue = mine.filter((j) => open(j) && new Date(j.scheduled_start) < startOfDay(today));

  return (
    <div className="phone">
      <h1>My jobs</h1>
      {error && <div className="error">{error}</div>}
      {overdue.length > 0 && (
        <>
          <h2>Earlier, not finished</h2>
          {overdue.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
        </>
      )}
      <h2>Today</h2>
      {todays.length === 0 ? <p className="muted">Nothing booked for today.</p> : todays.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
      <h2>Coming up</h2>
      {upcoming.length === 0 ? <p className="muted">No upcoming jobs.</p> : upcoming.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
    </div>
  );
}
