// Small spot illustrations for empty screens and the sign-in pages.
// Flat shapes in the app's own colours. Usage: <Spot kind="rest" />
const C = {
  spruce: "#0f5b57",
  deep: "#0a3f3c",
  wash: "#e4efed",
  signal: "#e8a317",
  paper: "#f4f5f2",
  line: "#c9d3cf",
  white: "#ffffff",
};

function House() {
  return (
    <>
      <ellipse cx="80" cy="112" rx="56" ry="7" fill={C.wash} />
      <path d="M36 62 80 26l44 36v46H36Z" fill={C.white} stroke={C.spruce} strokeWidth="3" strokeLinejoin="round" />
      <path d="M28 64 80 20l52 44" fill="none" stroke={C.spruce} strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="68" y="78" width="24" height="30" rx="3" fill={C.spruce} />
      <circle cx="87" cy="94" r="1.8" fill={C.signal} />
      <rect x="44" y="70" width="16" height="14" rx="2" fill={C.wash} stroke={C.spruce} strokeWidth="2" />
      <rect x="100" y="70" width="16" height="14" rx="2" fill={C.wash} stroke={C.spruce} strokeWidth="2" />
    </>
  );
}

function Sparkle({ x, y, s = 1 }) {
  return <path transform={`translate(${x} ${y}) scale(${s})`} d="M0-9 2.4-2.4 9 0 2.4 2.4 0 9-2.4 2.4-9 0-2.4-2.4Z" fill={C.signal} />;
}

function Person({ x, skin, hair, top, hairKind = "short" }) {
  return (
    <g transform={`translate(${x} 0)`}>
      <path d="M-24 112c0-22 10-36 24-36s24 14 24 36Z" fill={top} />
      <rect x="-5" y="66" width="10" height="12" rx="4" fill={skin} />
      <circle cx="0" cy="56" r="15" fill={skin} />
      {hairKind === "short" && <path d="M-15 54c0-12 8-18 15-18s15 6 15 18c-4-6-9-9-15-9s-11 3-15 9Z" fill={hair} />}
      {hairKind === "long" && <path d="M-16 58c-3-18 6-24 16-24s19 6 16 24c0-9-6-15-16-15s-16 6-16 15Z M-17 56h6v22h-6Z M11 56h6v22h-6Z" fill={hair} />}
      {hairKind === "curly" && <><circle cx="-9" cy="43" r="8" fill={hair} /><circle cx="0" cy="40" r="9" fill={hair} /><circle cx="9" cy="43" r="8" fill={hair} /></>}
      <circle cx="-5" cy="57" r="1.5" fill={C.deep} />
      <circle cx="5" cy="57" r="1.5" fill={C.deep} />
      <path d="M-4 63c2 2 6 2 8 0" fill="none" stroke={C.deep} strokeWidth="1.5" strokeLinecap="round" />
    </g>
  );
}

const VIEW = { team: "0 0 240 120" };

export default function Spot({ kind = "rest", className = "" }) {
  return (
    <svg className={`spot ${className}`} viewBox={VIEW[kind] || "0 0 160 120"} role="img" aria-label="" aria-hidden="true">
      {kind === "rest" && (
        <>
          <House />
          <Sparkle x={134} y={34} s={1.2} />
          <Sparkle x={24} y={46} s={0.8} />
          <Sparkle x={140} y={72} s={0.6} />
        </>
      )}
      {kind === "route" && (
        <>
          <ellipse cx="80" cy="112" rx="56" ry="7" fill={C.wash} />
          <path d="M26 98c24-4 18-34 40-34s14 28 38 24 22-30 34-38" fill="none" stroke={C.line} strokeWidth="3" strokeDasharray="2 8" strokeLinecap="round" />
          <circle cx="26" cy="98" r="6" fill={C.white} stroke={C.spruce} strokeWidth="3" />
          <path d="M138 50s16-13 16-27a16 16 0 1 0-32 0c0 14 16 27 16 27Z" transform="translate(-14 4) scale(.9)" fill={C.spruce} />
          <circle cx="127" cy="31" r="5.5" fill={C.signal} />
        </>
      )}
      {kind === "team" && (
        <>
          <ellipse cx="120" cy="114" rx="104" ry="6" fill={C.wash} />
          <Person x={62} skin="#8d5a3b" hair="#2b1d16" top={C.spruce} hairKind="curly" />
          <Person x={120} skin="#f0c9a4" hair="#7a4a22" top={C.signal} hairKind="long" />
          <Person x={178} skin="#c68a5e" hair="#1c1c1c" top={C.deep} hairKind="short" />
          <Sparkle x={34} y={30} s={0.9} />
          <Sparkle x={210} y={26} s={1.1} />
        </>
      )}
      {kind === "board" && (
        <>
          <ellipse cx="80" cy="112" rx="56" ry="7" fill={C.wash} />
          <rect x="22" y="22" width="116" height="82" rx="10" fill={C.white} stroke={C.spruce} strokeWidth="3" />
          <path d="M22 44h116" stroke={C.spruce} strokeWidth="3" />
          <rect x="32" y="54" width="28" height="14" rx="3" fill={C.wash} />
          <rect x="66" y="54" width="28" height="22" rx="3" fill={C.signal} opacity=".9" />
          <rect x="100" y="54" width="28" height="12" rx="3" fill={C.wash} />
          <rect x="32" y="74" width="28" height="20" rx="3" fill={C.spruce} opacity=".85" />
          <rect x="100" y="72" width="28" height="22" rx="3" fill={C.wash} />
          <circle cx="36" cy="33" r="3" fill={C.spruce} />
          <circle cx="48" cy="33" r="3" fill={C.signal} />
        </>
      )}
    </svg>
  );
}
