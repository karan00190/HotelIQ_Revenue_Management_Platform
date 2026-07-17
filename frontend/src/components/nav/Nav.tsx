"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Hotel } from "lucide-react";

import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/analytics", label: "Analytics" },
  { href: "/bookings", label: "Bookings" },
  { href: "/forecast", label: "Forecast" },
  { href: "/backtest", label: "ML Challenger" },
  { href: "/assistant", label: "Assistant" },
  { href: "/hotels", label: "Hotels" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-40 border-b border-white/5 bg-linear-to-r from-nav-bg via-nav-bg-accent to-nav-bg shadow-lg">
      <div className="flex w-full items-center gap-1 px-6 py-3 md:px-10">
        <Link href="/" className="mr-6 flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-linear-to-br from-brand-gold to-brand-gold-light text-nav-bg shadow-sm">
            <Hotel className="size-4" />
          </span>
          <span className="bg-linear-to-r from-brand-gold to-brand-gold-light bg-clip-text text-xl font-bold tracking-tight text-transparent">
            HotelIQ
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {LINKS.map((link) => {
            const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-nav-active font-medium text-nav-fg shadow-sm"
                    : "text-nav-muted hover:bg-white/5 hover:text-nav-fg"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
