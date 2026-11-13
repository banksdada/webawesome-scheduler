// Small line icons, drawn by hand so the app needs no icon library.
// Usage: <Icon name="calendar" size={20} />
const PATHS = {
  calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="2.5" /><path d="M3.5 10h17M8 3v4M16 3v4" /></>,
  board: <><rect x="3.5" y="4" width="7" height="16" rx="1.5" /><rect x="13.5" y="4" width="7" height="9" rx="1.5" /></>,
  alert: <><path d="M12 4 21 19H3Z" /><path d="M12 10v4M12 16.5v.5" /></>,
  phone: <><rect x="7" y="2.5" width="10" height="19" rx="2.5" /><path d="M11 18.5h2" /></>,
  bell: <><path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15Z" /><path d="M10 21h4" /></>,
  users: <><circle cx="9" cy="8.5" r="3.2" /><path d="M3 19c.6-3.3 3-5 6-5s5.4 1.7 6 5" /><circle cx="17" cy="9.5" r="2.4" /><path d="M17.5 14.2c2 .2 3.5 1.7 3.9 4.3" /></>,
  contact: <><rect x="3" y="5" width="18" height="14" rx="2.5" /><circle cx="9" cy="11" r="2" /><path d="M5.8 16c.5-1.6 1.7-2.4 3.2-2.4s2.7.8 3.2 2.4M14.5 10h3.5M14.5 13.5h3" /></>,
  quote: <><path d="M6 3.5h9l3 3V20.5H6Z" /><path d="M14.5 3.5V7H18M9 13h6M9 16.5h6" /></>,
  check: <><circle cx="12" cy="12" r="9" /><path d="m8 12.3 2.8 2.8L16 9.5" /></>,
  play: <><circle cx="12" cy="12" r="9" /><path d="m10.5 8.5 5 3.5-5 3.5Z" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  pound: <path d="M16 6.5a3.8 3.8 0 0 0-6.8 2.3V18M6.5 18h11M6.5 12.5H14" />,
  pin: <><path d="M12 21s6.5-5.6 6.5-11a6.5 6.5 0 1 0-13 0c0 5.4 6.5 11 6.5 11Z" /><circle cx="12" cy="10" r="2.3" /></>,
  inbox: <><path d="M4 13.5 6.5 5h11L20 13.5V19H4Z" /><path d="M4 13.5h4.5l1 2h5l1-2H20" /></>,
  sparkle: <path d="M12 3.5 13.8 10 20.5 12 13.8 14 12 20.5 10.2 14 3.5 12 10.2 10Z" />,
  building: <><rect x="5" y="3.5" width="14" height="17" rx="1.5" /><path d="M9 8h2M13 8h2M9 12h2M13 12h2M10 20.5v-4h4v4" /></>,
  mail: <><rect x="3" y="5.5" width="18" height="13" rx="2.5" /><path d="m4 7.5 8 6 8-6" /></>,
};

export default function Icon({ name, size = 20, className = "" }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}
