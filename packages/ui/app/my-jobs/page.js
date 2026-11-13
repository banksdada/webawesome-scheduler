"use client";

import { useCallback, useEffect, useState } from "react";
import { addDays, api, dayLabel, sameDay, startOfDay, timeOf } from "../lib/api";
import { useSession } from "../lib/useSession";
import Icon from "../components/Icon";
import Spot from "../components/Spot";

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
          {job.customer.phone ? <a href={`tel:${job.customer.phone}`}><Icon name="phone" size={18} />Call</a> : <span />}
          {maps ? <a href={maps} target="_blank" rel="noreferrer"><Icon name="pin" size={18} />Directions</a> : <span />}
        </div>
      )}
      {job.notes && <div className="note">{job.notes}</div>}
      {job.status === "assigned" && (
        <button className="big" disabled={busy} onClick={() => onAction(job, "start")}><Icon name="play" size={20} />Start job</button>
      )}
      {job.status === "in_progress" && (
        <button className="big finish" disabled={busy} onClick={() => onAction(job, "complete")}><Icon name="check" size={20} />Mark as done</button>
      )}
    </div>
  );
}

export default function MyJobs() {
  const { ready, session } = useSession();
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
  const todaysDone = todays.filter((j) => j.status === "done").length;
  const upcoming = mine.filter((j) => open(j) && new Date(j.scheduled_start) >= startOfDay(addDays(today, 1)));
  const overdue = mine.filter((j) => open(j) && new Date(j.scheduled_start) < startOfDay(today));

  return (
    <div className="phone">
      <h1>My jobs</h1>
      <div className="daycard">
        {todays.length === 0 ? (
          <Spot kind="rest" className="spot-sm" />
        ) : (
          <svg className="ring" viewBox="0 0 64 64" role="img" aria-label={`${todaysDone} of ${todays.length} done today`}>
            <circle cx="32" cy="32" r="26" fill="none" stroke="var(--spruce-wash)" strokeWidth="8" />
            <circle cx="32" cy="32" r="26" fill="none" stroke="var(--moss)" strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${(todaysDone / todays.length) * 163.4} 163.4`} transform="rotate(-90 32 32)" />
            <text x="32" y="37" textAnchor="middle" fontSize="17" fontWeight="700" fill="var(--ink)">{todaysDone}/{todays.length}</text>
          </svg>
        )}
        <div>
          <strong>{session?.name ? `Hello, ${session.name.split(" ")[0]}` : "Hello"}</strong>
          <span>{todays.length === 0 ? "Nothing booked for today." : todaysDone === todays.length ? "All done for today. Thank you, nice work." : `${todays.length - todaysDone} still to do today.`}</span>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {overdue.length > 0 && (
        <>
          <h2>Earlier, not finished</h2>
          {overdue.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
        </>
      )}
      <h2>Today</h2>
      {todays.length === 0 ? null : todays.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
      <h2>Coming up</h2>
      {upcoming.length === 0 ? <div className="emptyspot"><Spot kind="route" className="spot-sm" /><p className="muted">No upcoming jobs.</p></div> : upcoming.map((j) => <JobCard key={j.id} job={j} onAction={act} busy={busy} />)}
    </div>
  );
}
