"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "./api";

// Reads the login on the page. If `role` is given, other people are sent elsewhere.
export function useSession({ role } = {}) {
  const router = useRouter();
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const s = getSession();
    if (!s) {
      router.replace("/login");
      return;
    }
    if (role && s.role !== role) {
      router.replace(s.role === "admin" ? "/schedule" : "/my-jobs");
      return;
    }
    setSession(s);
    setReady(true);
  }, [router, role]);

  return { session, ready };
}
