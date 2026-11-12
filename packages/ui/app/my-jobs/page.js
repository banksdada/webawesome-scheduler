"use client";

import { useCallback, useEffect, useState } from "react";
import { addDays, api, dayLabel, sameDay, startOfDay, timeOf } from "../lib/api";
import { useSession } from "../lib/useSession";

function JobCard({ job, onAction, busy }) {
  const maps = job.customer.address
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(job.customer.address)}`
    : null;
  return (
    <div className="jobcard">
      <h3>{job.title}</h3>
      <div>
        {job.scheduled_start ? `${dayLabel(new Date(job.scheduled_start))}, ${timeOf(job.scheduled_start)}` : "No time set"} ·{" "}
        {job.duration_minutes} min <span className="badge">{job.status.replace("_", " ")}</span>
      </div>
      <p style={{ margin: ".5rem 0 0" }}><strong>{job.customer.name}</strong></p>
      {job.customer.address && <div>{job.customer.address}</div>}
      <div>
        {job.customer.phone && <a className="action" href={`tel:${job.customer.phone}`}>Call {job.customer.phone}</a>}
        {maps && <a className="action" href={maps} target="_blank" rel="noreferrer">Open in Maps</a>}
      </div>
      {job.notes && <p className="muted">Notes: {job.notes}</p>}
      {job.status === "assigned" && (
        <button className="big" disabled={busy} onClick={() => onAction(job, "start")}>Start job</button>
      )}
      {job.status === "in_progress" && (
        <button className="big" disabled={busy} onClick={() => onAction(job, "complete")}>Mark as done</button>
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
    <>
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
    </>
  );
}
