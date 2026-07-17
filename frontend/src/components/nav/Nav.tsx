"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Hotel, Menu, X } from "lucide-react";

import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analytics", label: "Analytics" },
  { href: "/bookings", label: "Bookings" },
  { href: "/forecast", label: "Forecast" },
  { href: "/backtest", label: "ML Challenger" },
  { href: "/assistant", label: "Assistant" },
  { href: "/hotels", label: "Hotels" },
];

function isLinkActive(href: string, pathname: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-40 border-b border-white/5 bg-linear-to-r from-nav-bg via-nav-bg-accent to-nav-bg shadow-lg">
      <div className="flex w-full items-center gap-1 px-4 py-3 sm:px-6 md:px-10">
        <Link href="/" className="mr-4 flex items-center gap-2 lg:mr-6" onClick={() => setOpen(false)}>
          <span className="flex size-8 items-center justify-center rounded-lg bg-linear-to-br from-brand-gold to-brand-gold-light text-nav-bg shadow-sm">
            <Hotel className="size-4" />
          </span>
          <span className="bg-linear-to-r from-brand-gold to-brand-gold-light bg-clip-text text-xl font-bold tracking-tight text-transparent">
            HotelIQ
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-1 lg:flex">
          {LINKS.map((link) => {
            const isActive = isLinkActive(link.href, pathname);
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

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            className="flex size-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-nav-fg transition-all duration-200 hover:bg-white/15 lg:hidden"
          >
            {open ? <X className="size-4.5" /> : <Menu className="size-4.5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="border-t border-white/5 px-3 pb-3 pt-1 duration-200 animate-in fade-in slide-in-from-top-2 lg:hidden">
          <div className="flex flex-col gap-0.5">
            {LINKS.map((link) => {
              const isActive = isLinkActive(link.href, pathname);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className={`rounded-md px-3 py-2.5 text-sm transition-all duration-200 ${
                    isActive
                      ? "bg-nav-active font-medium text-nav-fg"
                      : "text-nav-muted hover:bg-white/5 hover:text-nav-fg"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
}
