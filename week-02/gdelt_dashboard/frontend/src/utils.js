// Форматирование дат GDELT (строка вида "20260722143000") в читаемый вид.

export function formatGdeltDateTime(raw) {
  if (!raw || raw.length < 12) return raw || "";
  const y = raw.slice(0, 4);
  const mo = raw.slice(4, 6);
  const d = raw.slice(6, 8);
  const h = raw.slice(8, 10);
  const mi = raw.slice(10, 12);
  return `${d}.${mo}.${y} ${h}:${mi}`;
}

export function formatGdeltDay(raw) {
  if (!raw || raw.length < 8) return raw || "";
  const y = raw.slice(0, 4);
  const mo = raw.slice(4, 6);
  const d = raw.slice(6, 8);
  return `${d}.${mo}.${y}`;
}

export function formatGdeltDayShort(raw) {
  if (!raw || raw.length < 8) return raw || "";
  const mo = raw.slice(4, 6);
  const d = raw.slice(6, 8);
  return `${d}.${mo}`;
}

// input[type=date] отдаёт "2026-07-22" -> нужно "20260722000000" / "...235959"
export function inputDateToGdelt(value, endOfDay = false) {
  if (!value) return "";
  const digits = value.replaceAll("-", "");
  return digits + (endOfDay ? "235959" : "000000");
}

// Обратное преобразование для value инпута <input type="date">
export function gdeltToInputDate(raw) {
  if (!raw || raw.length < 8) return "";
  return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`;
}

export function toneClass(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "tone-neutral";
  const v = Number(value);
  if (v > 0.5) return "tone-positive";
  if (v < -0.5) return "tone-negative";
  return "tone-neutral";
}
