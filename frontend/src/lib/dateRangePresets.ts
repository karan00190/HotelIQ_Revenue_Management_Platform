export type PresetKey = "7d" | "30d" | "90d" | "month";

export const PRESETS: { key: PresetKey; label: string }[] = [
  { key: "7d", label: "Last 7 days" },
  { key: "30d", label: "Last 30 days" },
  { key: "90d", label: "Last 90 days" },
  { key: "month", label: "This month" },
];

function toIso(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function computeRange(preset: PresetKey): { startDate: string; endDate: string } {
  const now = new Date();
  const endDate = toIso(now);

  if (preset === "month") {
    return { startDate: toIso(new Date(now.getFullYear(), now.getMonth(), 1)), endDate };
  }
  const days = preset === "7d" ? 7 : preset === "30d" ? 30 : 90;
  const start = new Date(now);
  start.setDate(start.getDate() - days);
  return { startDate: toIso(start), endDate };
}
