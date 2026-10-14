import type { Column, Row } from "./types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function timeLabel(value: string, granularity?: string): string {
  const [y, m, d] = value.slice(0, 10).split("-").map(Number);
  switch (granularity) {
    case "year": return String(y);
    case "quarter": return `${y} Q${Math.floor((m - 1) / 3) + 1}`;
    case "month": return `${MONTHS[m - 1]} ${y}`;
    default: return `${MONTHS[m - 1]} ${d}, ${y}`;
  }
}

const currencyCompact = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 2 });
const currencyFull = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const plain = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

export function formatValue(v: string | number | null | undefined, col: Column, compact = false): string {
  if (v === null || v === undefined) return "-";
  if (col.kind === "time") return timeLabel(String(v), col.granularity);
  if (typeof v !== "number") return String(v);
  if (col.format === "percent") return `${(v * 100).toFixed(1)}%`;
  if (col.format === "currency") return (compact ? currencyCompact : currencyFull).format(v);
  return plain.format(v);
}

export function cellText(row: Row, col: Column, compact = false): string {
  return formatValue(row[col.key], col, compact);
}
