import { describe, expect, it } from "vitest";

import { formatDateShort, parseLocalDate } from "./date";

describe("parseLocalDate", () => {
  // The whole reason this helper exists: new Date("2026-01-15") parses as UTC
  // midnight, which rolls back to Jan 14 in any timezone behind UTC. Parsing
  // the parts and building a LOCAL date must always give the calendar date as
  // written, regardless of the runner's timezone. This test guards that fix.
  it("returns the calendar date as written, not a UTC-shifted one", () => {
    const d = parseLocalDate("2026-01-15");
    expect(d.getFullYear()).toBe(2026);
    expect(d.getMonth()).toBe(0); // January (0-indexed)
    expect(d.getDate()).toBe(15); // never 14
  });

  it("handles mid-year dates", () => {
    const d = parseLocalDate("2025-12-05");
    expect(d.getMonth()).toBe(11); // December
    expect(d.getDate()).toBe(5);
  });
});

describe("formatDateShort", () => {
  it("formats to a short 'MMM D' style label", () => {
    // en-IN short month + numeric day. Exact punctuation varies by ICU, so
    // assert on the meaningful parts rather than an exact string.
    const label = formatDateShort("2025-12-05");
    expect(label).toContain("Dec");
    expect(label).toContain("5");
  });
});
