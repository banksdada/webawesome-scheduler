"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { clearSession, getSession } from "../lib/api";
import Icon from "./Icon";

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

  const on = (href) => (pathname && pathname.startsWith(href) ? "active" : "");

  return (
    <nav className="nav">
      <span className="brand"><span className="mark" aria-hidden="true" />WebAwesome Scheduler</span>
      {session?.role === "admin" && !session.platform_admin && (
        <>
          <Link href="/schedule" className={on("/schedule")}><Icon name="calendar" size={17} />Schedule</Link>
          <Link href="/customers" className={on("/customers")}><Icon name="contact" size={17} />Customers</Link>
          <Link href="/team" className={on("/team")}><Icon name="users" size={17} />Team</Link>
        </>
      )}
      {session?.platform_admin && <Link href="/platform" className={on("/platform")}><Icon name="building" size={17} />Platform</Link>}
      {session && !session.platform_admin && <Link href="/my-jobs" className={on("/my-jobs")}><Icon name="phone" size={17} />My jobs</Link>}
      {session ? (
        <>
          <span className="who">{session.name}</span>
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
