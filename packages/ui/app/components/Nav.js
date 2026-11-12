"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clearSession, getSession } from "../lib/api";

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const [session, setSession] = useState(null);

  useEffect(() => {
    setSession(getSession());
  }, [pathname]);

  function signOut() {
    clearSession();
    setSession(null);
    router.push("/login");
  }

  return (
    <nav className="nav">
      <span className="brand">WebAwesome Scheduler</span>
      {session?.role === "admin" && (
        <>
          <Link href="/schedule">Schedule</Link>
          <Link href="/customers">Customers</Link>
          <Link href="/team">Team</Link>
        </>
      )}
      {session && <Link href="/my-jobs">My jobs</Link>}
      {session ? (
        <>
          <span className="muted" style={{ color: "#ccd" }}>{session.name}</span>
          <button onClick={signOut}>Sign out</button>
        </>
      ) : (
        <>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Sign up</Link>
        </>
      )}
    </nav>
  );
}
