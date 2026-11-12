// Talks to the API. NEXT_PUBLIC_API_URL is baked in when the site is built.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const KEY = "scheduler_session";

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "null");
  } catch {
    return null;
  }
}

export function saveSession(session) {
  localStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(KEY);
}

// Returns the parsed JSON. Throws an Error with .status and .detail when the API says no.
export async function api(path, { method = "GET", body, form } = {}) {
  const session = getSession();
  const headers = {};
  if (session?.token) headers.Authorization = `Bearer ${session.token}`;
  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, { method, headers, body: payload });
  } catch {
    const err = new Error("Cannot reach the server. Check your internet connection and try again.");
    err.status = 0;
    throw err;
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    let message = "Something went wrong";
    if (typeof detail === "string") message = detail;
    else if (detail?.message) message = detail.message;
    else if (Array.isArray(detail) && detail[0]?.msg) message = detail[0].msg;
    const err = new Error(message);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }
  return data;
}

// ---- date helpers (the API sends UTC, people see their own time) ----
export function toLocalInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function fromLocalInput(value) {
  return value ? new Date(value).toISOString() : null;
}

export function timeOf(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function dayLabel(date) {
  return date.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}

export function startOfDay(date) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

export function startOfWeek(date) {
  const d = startOfDay(date);
  const day = (d.getDay() + 6) % 7; // Monday = 0
  return addDays(d, -day);
}

export function sameDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}
