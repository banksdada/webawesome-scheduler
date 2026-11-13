"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "./lib/api";

const STEPS = [
  { title: "Book the job", text: "Pick the customer, set the time and how long it should take. Add access notes the technician will need on the doorstep." },
  { title: "Assign it", text: "Choose who's going. If that person is already booked, you're warned about the clash before you save." },
  { title: "Get it done", text: "The technician gets an email, opens their phone view, taps Start and Done. You see the status on the board." },
];

const FEATURES = [
  { title: "Week board", text: "Every job for the week in one view, filtered by technician when you want to focus on one person." },
  { title: "Clash warnings", text: "Double-booking a technician is caught as you schedule, so you can move the job or override it on purpose." },
  { title: "Technician phone view", text: "Today's jobs first, with the address, a call button, directions, access notes and a big Start button." },
  { title: "Email when it changes", text: "Technicians are emailed when a job is assigned to them or moved, so nobody is working from an old message." },
  { title: "Customer records", text: "Names, phone numbers, addresses and notes like pets or parking, kept with the customer and shown on every job." },
  { title: "Quote from the job", text: "Add a price estimate to a job and open a clean, printable quote for the customer." },
];

const WHO = [
  { title: "Cleaning and pest control", text: "Crews moving between homes and sites all day, with different jobs for different people." },
  { title: "Home care and support", text: "Visits that need the right person at the right address, at the right time." },
  { title: "Any team that visits customers", text: "If someone has to turn up somewhere, the board shows who, where and when." },
];

function BoardMock() {
  const job = (time, title, cust, who, cls = "") => (
    <div className={`job ${cls}`}>
      <div className="time">{time}</div>
      <div className="title">{title}</div>
      <div className="cust">{cust}</div>
      <div className="foot"><span className="avatar">{who.split(" ").map((w) => w[0]).join("")}</span><span>{who}</span></div>
    </div>
  );
  const head = (dow, num) => (
    <div className="dayhead"><span className="dow">{dow}</span><span className="num">{num}</span></div>
  );
  return (
    <div className="mk-mock" aria-hidden="true">
      <div className="mk-board">
        <div className="day">{head("Mon", 9)}{job("08:30", "Deep clean, 3 bed", "Mrs Okafor", "Sam Rivera")}{job("13:00", "Wasp nest removal", "Hartley Dental", "Priya Nair")}</div>
        <div className="day today">{head("Tue", 10)}{job("09:00", "Weekly office clean", "Northgate Surgery", "Sam Rivera", "in_progress")}{job("14:30", "Morning visit", "Mr Bell", "Priya Nair")}</div>
        <div className="day">{head("Wed", 11)}{job("10:00", "Move-out clean", "14 Elm Road", "Sam Rivera")}</div>
      </div>
      <div className="mk-phone">
        <div className="mk-notch" />
        <div className="jobcard in_progress">
          <div className="when"><span className="t">09:00</span><span className="d">Tue · 60 min</span></div>
          <h3>Weekly office clean</h3>
          <div><strong>Northgate Surgery</strong></div>
          <div className="addr">2 Park Row, Leeds</div>
          <div className="actions"><a>Call</a><a>Directions</a></div>
          <button className="big finish" tabIndex={-1}>Mark as done</button>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const s = getSession();
    if (s) router.replace(s.platform_admin ? "/platform" : s.role === "admin" ? "/schedule" : "/my-jobs");
    else setReady(true);
  }, [router]);

  if (!ready) return <p className="muted">Loading...</p>;

  return (
    <div className="mk">
      <section className="mk-hero">
        <div className="mk-copy">
          <h1>Every job on the board. Every technician on the way.</h1>
          <p className="mk-lead">
            Schedule jobs, assign them to your team and send each technician their work by email. They get a phone view with the address,
            the notes and a Start button. You get a week board that shows what's happening.
          </p>
          <div className="mk-cta">
            <Link href="/signup" className="btn mk-primary">Create your account</Link>
            <Link href="/login" className="btn secondary mk-secondary">Log in</Link>
          </div>
        </div>
        <BoardMock />
      </section>

      <section className="mk-section">
        <h2>How a job moves through your day</h2>
        <ol className="mk-steps">
          {STEPS.map((s, i) => (
            <li key={s.title}>
              <span className="mk-step-n">{i + 1}</span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mk-section">
        <h2>What you get</h2>
        <div className="mk-features">
          {FEATURES.map((f) => (
            <div key={f.title} className="mk-feature">
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mk-section">
        <h2>Made for teams that go to the customer</h2>
        <div className="mk-who">
          {WHO.map((w) => (
            <div key={w.title}>
              <h3>{w.title}</h3>
              <p>{w.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mk-band">
        <h2>Put this week on the board</h2>
        <p>Create an account, add a customer and a technician, and schedule your first job in a few minutes.</p>
        <Link href="/signup" className="btn mk-primary">Create your account</Link>
      </section>

      <footer className="mk-foot">
        <span>WebAwesome Scheduler</span>
        <Link href="/login">Log in</Link>
      </footer>
    </div>
  );
}
