"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession } from "./lib/api";

// The front door just sends you to the right place.
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const s = getSession();
    router.replace(!s ? "/login" : s.role === "admin" ? "/schedule" : "/my-jobs");
  }, [router]);
  return <p className="muted">Loading...</p>;
}
