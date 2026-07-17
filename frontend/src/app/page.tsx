import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Boxes,
  BrainCircuit,
  Code2,
  Cpu,
  Database,
  Layers,
  LineChart,
  MessageSquareText,
  ScrollText,
  Server,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

import { Reveal } from "@/components/about/Reveal";

export const metadata = {
  title: "HotelIQ · AI-Powered Revenue Management",
  description:
    "HotelIQ turns raw hotel bookings into demand forecasts, AI-guided pricing, and a conversational assistant — every number traced back to a real calculation.",
};

const STATS = [
  { value: "3", label: "demo hotels" },
  { value: "2 yrs", label: "of daily data" },
  { value: "13", label: "AI assistant tools" },
  { value: "0.7–1.5×", label: "pricing range" },
];

const LAYERS = [
  {
    icon: Workflow,
    accent: "var(--chart-1)",
    title: "Process layer",
    desc: "Every booking is validated against nine data-quality checks — required fields, parseable dates, logical ordering, positive prices, duplicate and outlier detection — before it ever reaches the database.",
  },
  {
    icon: BarChart3,
    accent: "var(--chart-2)",
    title: "Analytics layer",
    desc: "Daily occupancy, ADR and RevPAR are pre-computed for every hotel and every day into a metrics table, so dashboard reads never have to re-scan raw bookings.",
  },
  {
    icon: BrainCircuit,
    accent: "var(--chart-4)",
    title: "AI layer",
    desc: "Reads only the clean, pre-aggregated history to forecast demand, recommend prices, and power a conversational assistant — never touching raw bookings directly.",
  },
];

const PRICING_FACTORS = [
  { k: "Predicted occupancy", v: "The strongest lever — up to +40% at 90%+ demand, a discount below 40%." },
  { k: "Current occupancy", v: "A scarcity premium when nearly full, a nudge-down discount when nearly empty." },
  { k: "Weekend", v: "A flat premium for Friday / Saturday check-ins." },
  { k: "Peak season", v: "A flat premium across the October–February high season." },
  { k: "Lead time", v: "A last-minute premium, an early-bird discount for booking far ahead." },
];

const STACK = [
  { group: "Backend", items: ["Python 3.10", "FastAPI", "SQLAlchemy", "Pandas", "SQLite"] },
  { group: "ML & AI", items: ["Prophet", "XGBoost", "LangChain", "LangGraph", "ChromaDB", "Groq", "Gemini embeddings"] },
  { group: "Frontend", items: ["Next.js 16", "React 19", "TypeScript", "Tailwind v4", "TanStack Query", "Recharts"] },
  { group: "Infrastructure", items: ["Docker", "Render", "Vercel"] },
];

function IconChip({ icon: Icon, accent }: { icon: typeof Layers; accent: string }) {
  return (
    <span
      className="flex size-11 shrink-0 items-center justify-center rounded-xl text-white shadow-md ring-1 ring-white/15"
      style={{ background: `linear-gradient(135deg, ${accent}, color-mix(in oklab, ${accent} 55%, #000))` }}
    >
      <Icon className="size-5" />
    </span>
  );
}

function SectionHeading({
  icon,
  accent,
  eyebrow,
  title,
}: {
  icon: typeof Layers;
  accent: string;
  eyebrow: string;
  title: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <IconChip icon={icon} accent={accent} />
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{eyebrow}</p>
        <h2 className="text-xl font-semibold tracking-tight text-foreground sm:text-2xl">{title}</h2>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="w-full">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/5 bg-linear-to-br from-nav-bg via-nav-bg-accent to-nav-bg text-nav-fg">
        <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="animate-float-slow absolute -left-20 -top-24 size-80 rounded-full bg-chat-user-from/20 blur-3xl" />
          <div className="animate-float-slow absolute -right-16 top-10 size-72 rounded-full bg-brand-gold/15 blur-3xl [animation-delay:-3s]" />
          <div className="animate-float-slow absolute bottom-0 left-1/3 size-72 rounded-full bg-chat-user-to/20 blur-3xl [animation-delay:-6s]" />
        </div>

        <div className="relative mx-auto flex max-w-5xl flex-col items-start gap-6 px-5 py-16 sm:px-8 md:py-24">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-medium text-nav-fg duration-500 animate-in fade-in slide-in-from-bottom-2">
            <Sparkles className="size-3.5 text-brand-gold-light" />
            Full-stack hotel revenue platform
          </span>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight duration-700 animate-in fade-in slide-in-from-bottom-3 sm:text-5xl md:text-6xl">
            From raw bookings to{" "}
            <span className="bg-linear-to-r from-brand-gold to-brand-gold-light bg-clip-text text-transparent">
              AI-guided pricing
            </span>
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-nav-muted duration-700 animate-in fade-in slide-in-from-bottom-4 sm:text-lg">
            HotelIQ is an end-to-end revenue management system. It ingests and validates booking data, pre-computes the
            metrics that matter, forecasts demand with two competing models, turns those forecasts into concrete price
            recommendations, and lets a manager ask questions in plain language — with every number traced back to a real
            calculation.
          </p>
          <div className="flex flex-wrap gap-3 pt-1 duration-700 animate-in fade-in slide-in-from-bottom-5">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-lg bg-linear-to-r from-brand-gold to-brand-gold-light px-5 py-2.5 text-sm font-semibold text-nav-bg shadow-md transition-all hover:opacity-90"
            >
              Launch the dashboard
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/assistant"
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 bg-white/5 px-5 py-2.5 text-sm font-medium text-nav-fg backdrop-blur-sm transition-all hover:bg-white/15"
            >
              <Sparkles className="size-4" />
              Try the assistant
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 pt-4 duration-700 animate-in fade-in slide-in-from-bottom-6 sm:grid-cols-4">
            {STATS.map((s) => (
              <div key={s.label} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-sm">
                <p className="text-2xl font-bold text-nav-fg">{s.value}</p>
                <p className="text-xs text-nav-muted">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="mx-auto flex max-w-5xl flex-col gap-16 px-5 py-14 sm:px-8 md:gap-24 md:py-20">
        {/* The problem */}
        <Reveal className="flex flex-col gap-4">
          <SectionHeading icon={Activity} accent="var(--chart-3)" eyebrow="The problem" title="Why revenue management matters" />
          <p className="max-w-3xl text-base leading-relaxed text-muted-foreground">
            A hotel room is the most perishable product there is — an empty room tonight can never be sold again. The core
            metric, RevPAR (revenue per available room), depends on getting <span className="font-medium text-foreground">both</span>{" "}
            price and occupancy right at the same time. Price too high and rooms sit empty; too low and money is left on the
            table. HotelIQ predicts how full each hotel will be, then turns that prediction into a specific recommended price
            — the way a real revenue team would, but automatically and explainably.
          </p>
        </Reveal>

        {/* Architecture */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={Layers} accent="var(--chart-1)" eyebrow="Architecture" title="Three layers, one clean flow" />
          <div className="grid gap-4 md:grid-cols-3">
            {LAYERS.map((layer, i) => (
              <Reveal key={layer.title} delay={i * 90}>
                <div className="group h-full rounded-2xl border border-border bg-card p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md">
                  <IconChip icon={layer.icon} accent={layer.accent} />
                  <h3 className="mt-4 text-base font-semibold text-foreground">{layer.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{layer.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* Data pipeline */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={Database} accent="var(--chart-2)" eyebrow="Data pipeline" title="ETL built to be trusted" />
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">Realistic synthetic data</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                The demo dataset spans two full years across three hotels. Booking arrival rates — not just prices —
                genuinely respond to weekends and seasons, and each room&rsquo;s stays are walked forward day by day so
                occupancy can never mathematically exceed 100%. That gives the forecasting models real seasonal signal to
                learn from rather than noise.
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">Validation &amp; feature engineering</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Nine data-quality checks gate every record before it lands. Feature engineering adds calendar signals, real
                Indian public holidays, and lag / rolling occupancy features — all computed on the full chronological series
                and shifted so a day&rsquo;s features never peek at its own value. Leakage-safe by construction.
              </p>
            </div>
          </div>
        </Reveal>

        {/* Forecasting */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={LineChart} accent="var(--chart-4)" eyebrow="Forecasting" title="Two models, evaluated head-to-head" />
          <p className="max-w-3xl text-base leading-relaxed text-muted-foreground">
            HotelIQ runs two independent forecasters that predict the same thing — daily occupancy — so they can be compared
            fairly. <span className="font-medium text-foreground">Prophet</span> decomposes each hotel&rsquo;s history into
            trend and seasonality. <span className="font-medium text-foreground">XGBoost</span>, the challenger, is a
            gradient-boosted tree trained once, pooled across all hotels, on explicit engineered features.
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <p className="text-2xl font-bold text-foreground">25–35%</p>
              <p className="mt-1 text-sm text-muted-foreground">lower forecast error (MAE) for XGBoost, per hotel.</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <p className="text-2xl font-bold text-foreground">Strict split</p>
              <p className="mt-1 text-sm text-muted-foreground">Time-based holdout, never shuffled — a forecast can only use the past.</p>
            </div>
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <p className="text-2xl font-bold text-foreground">1,000×</p>
              <p className="mt-1 text-sm text-muted-foreground">bootstrap resamples for honest revenue-impact confidence bands.</p>
            </div>
          </div>
          <div className="rounded-2xl border border-border bg-linear-to-br from-assistant-bubble/50 via-card to-assistant-bubble-2/40 p-6 shadow-sm">
            <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
              <ScrollText className="size-4 text-assistant-glow" />
              A genuinely interesting finding
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              XGBoost is the more accurate forecaster on every property — but that does not always translate into more
              simulated revenue. The pricing engine reacts through discrete tiers, so two forecasts that land in the same
              tier produce an identical price regardless of which was numerically closer. HotelIQ reports this openly rather
              than hiding it behind a simpler &ldquo;our model is better&rdquo; story.
            </p>
          </div>
        </Reveal>

        {/* Pricing engine */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={Boxes} accent="var(--chart-5)" eyebrow="Pricing" title="An explainable pricing engine" />
          <p className="max-w-3xl text-base leading-relaxed text-muted-foreground">
            The pricing engine is not a black box — it is a set of published, multiplicative factors that take a demand
            forecast and turn it into one concrete price, with the total multiplier clipped between 0.7× and 1.5× so no
            combination can push a price to an extreme. Every recommendation comes with a plain-language explanation of
            exactly which factors fired.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {PRICING_FACTORS.map((f, i) => (
              <Reveal key={f.k} delay={i * 70}>
                <div className="flex h-full gap-3 rounded-xl border border-border bg-card p-4 shadow-sm">
                  <span className="mt-1 size-2 shrink-0 rounded-full" style={{ background: "var(--chart-5)" }} />
                  <div>
                    <p className="text-sm font-semibold text-foreground">{f.k}</p>
                    <p className="mt-0.5 text-sm text-muted-foreground">{f.v}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* AI assistant */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={MessageSquareText} accent="var(--chat-user-to)" eyebrow="Conversational AI" title="An assistant that never guesses a number" />
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">Tools for data, search for explanations</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                A LangChain agent answers questions two ways. Anything numeric — revenue, occupancy, a forecast, a price —
                is answered by calling one of 13 real tools that run the same code the dashboard uses. Anything conceptual —
                &ldquo;what is RevPAR?&rdquo; — is answered by searching a small knowledge base. The two never mix.
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">Free-tier by design</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                It runs on Groq&rsquo;s free tier for chat and Gemini&rsquo;s free embeddings API. Those embeddings are
                computed once and committed to the repo, so the vector index builds at container-build time with no secrets
                and no runtime embedding cost. Every real number is traceable to a specific tool call shown in the interface.
              </p>
            </div>
          </div>
        </Reveal>

        {/* Honesty */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={ShieldCheck} accent="var(--chart-2)" eyebrow="Methodology" title="Honesty as a design principle" />
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                t: "No false causality",
                d: "The system never claims to predict how price changes demand. The data only records bookings that happened — a price-elasticity model would fit noise, so it is deliberately not built.",
              },
              {
                t: "Assumptions stated plainly",
                d: "The revenue backtest assumes guests would have booked anyway at the recommended price. That single assumption is printed next to every number, not buried in a footnote.",
              },
              {
                t: "Zero-hallucination assistant",
                d: "If a tool errors, the assistant says so plainly rather than inventing a plausible answer. An honest ‘I don’t have that’ is always the correct response.",
              },
            ].map((c, i) => (
              <Reveal key={c.t} delay={i * 90}>
                <div className="h-full rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-foreground">{c.t}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{c.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* Tech stack */}
        <Reveal className="flex flex-col gap-6">
          <SectionHeading icon={Cpu} accent="var(--chart-1)" eyebrow="Under the hood" title="Technology" />
          <div className="grid gap-4 sm:grid-cols-2">
            {STACK.map((s, i) => (
              <Reveal key={s.group} delay={i * 80}>
                <div className="h-full rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <Server className="size-4 text-muted-foreground" />
                    {s.group}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {s.items.map((item) => (
                      <span
                        key={item}
                        className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs text-foreground"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </Reveal>

        {/* CTA */}
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-linear-to-br from-nav-bg via-nav-bg-accent to-nav-bg p-8 text-nav-fg shadow-lg sm:p-10">
            <div aria-hidden className="animate-float-slow pointer-events-none absolute -right-10 -top-10 size-56 rounded-full bg-brand-gold/15 blur-3xl" />
            <div className="relative flex flex-col items-start gap-4">
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">See it in action</h2>
              <p className="max-w-xl text-sm leading-relaxed text-nav-muted">
                Explore live dashboards, compare the two forecasting models on real held-out data, or just ask the
                assistant a question in plain English.
              </p>
              <div className="flex flex-wrap gap-3 pt-1">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-linear-to-r from-brand-gold to-brand-gold-light px-4 py-2 text-sm font-semibold text-nav-bg shadow-sm transition-all hover:opacity-90"
                >
                  Open the dashboard
                  <ArrowRight className="size-4" />
                </Link>
                <Link
                  href="/assistant"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium text-nav-fg transition-all hover:bg-white/15"
                >
                  <Sparkles className="size-4" />
                  Try the assistant
                </Link>
                <a
                  href="https://github.com/karan00190/HotelIQ_Revenue_Management_Platform"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium text-nav-fg transition-all hover:bg-white/15"
                >
                  <Code2 className="size-4" />
                  View the code
                </a>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
