// Gives each person a steady colour, so "Sam" is always the same colour on the board.
export function toneFor(name = "") {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) % 997;
  return h % 6;
}
