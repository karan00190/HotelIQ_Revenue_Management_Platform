// new Date("YYYY-MM-DD") parses as UTC midnight, so .getDay()/.getDate() can
// silently roll back a day in any timezone behind UTC. Parsing the parts
// directly and constructing a local Date avoids that off-by-one.
export function parseLocalDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function formatDateShort(dateStr: string): string {
  return parseLocalDate(dateStr).toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}
