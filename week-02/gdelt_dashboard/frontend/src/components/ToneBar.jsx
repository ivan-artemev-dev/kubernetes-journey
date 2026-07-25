import { toneClass } from "../utils.js";

export default function ToneBar({ value }) {
  if (value === null || value === undefined) {
    return <span className="tone-badge tone-neutral">—</span>;
  }
  const v = Number(value);
  return <span className={`tone-badge ${toneClass(v)}`}>{v > 0 ? "+" : ""}{v.toFixed(1)}</span>;
}
