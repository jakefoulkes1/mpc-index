import { AnimatePresence, motion, useReducedMotion, type PanInfo } from 'framer-motion';
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Factory,
  Handshake,
  HardHat,
  HeartPulse,
  Landmark,
  Plus,
  Rocket,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useEffect, useState, type MouseEvent } from 'react';
import { Link } from 'react-router-dom';
import { DrawnLine, ScrollSpine, Underline } from '../components/BrightLine';
import { CountUp } from '../components/CountUp';
import { usePageTitle } from '../components/Layout';
import { Avatar, Monogram } from '../components/Monogram';
import { ParticleField } from '../components/ParticleField';
import { Reveal, SectionHeading } from '../components/Reveal';
import { companies, sectors, steps, team } from '../data';
import { StatusPill } from '../components/StatusPill';
import { cn } from '../lib/utils';

export default function Home() {
  usePageTitle('');
  return (
    <>
      <Hero />
      <ScrollSpine>
        <Problem />
        <Edge />
        <Numbers />
        <Process />
        <PortfolioPreview />
        <TeamPreview />
        <CtaBand />
      </ScrollSpine>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* 1. Hero                                                             */
/* ------------------------------------------------------------------ */

function Hero() {
  const reduce = useReducedMotion();
  const ease = [0.22, 1, 0.36, 1] as const;
  const fade = (delay: number) => ({
    initial: { opacity: 0, y: reduce ? 0 : 24 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: reduce ? 0.2 : 0.8, delay: reduce ? 0 : delay, ease },
  });

  const toPortfolio = (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const el = document.getElementById('portfolio');
    el?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    history.replaceState(null, '', '#portfolio');
    window.setTimeout(() => el?.focus({ preventScroll: true }), reduce ? 0 : 700);
  };

  return (
    <section className="relative flex min-h-[100svh] flex-col justify-center overflow-hidden pb-20 pt-32" aria-labelledby="hero-title">
      <div className="absolute inset-0 bg-grid opacity-70 [mask-image:radial-gradient(ellipse_70%_60%_at_60%_40%,black,transparent)]" aria-hidden="true" />
      <ParticleField />
      <div className="absolute right-[-10%] top-[-20%] h-[640px] w-[640px] rounded-full bg-amber/[0.06] blur-3xl" aria-hidden="true" />
      <div className="absolute bottom-[-30%] left-[-10%] h-[520px] w-[520px] rounded-full bg-[#2B4C7E]/30 blur-3xl" aria-hidden="true" />

      <div className="container-site relative">
        <motion.p className="eyebrow" {...fade(0)}>
          Fund I · Series A &amp; B
        </motion.p>
        <motion.h1 id="hero-title" className="mt-7 max-w-5xl text-balance text-[2.7rem] font-bold leading-[1.02] text-paper sm:text-6xl lg:text-[5.4rem]" {...fade(0.1)}>
          Backing AI that runs the <span className="text-amber [text-shadow:0_0_40px_rgba(242,179,61,.35)]">real economy.</span>
        </motion.h1>
        <motion.p className="mt-7 max-w-2xl text-lg leading-relaxed text-slate-light sm:text-xl" {...fade(0.25)}>
          A $250M fund for growing companies that use AI to automate how energy, manufacturing, healthcare and finance actually work.
        </motion.p>
      </div>

      <DrawnLine className="relative mt-10 h-16 sm:mt-12 sm:h-20" delay={reduce ? 0 : 0.55} duration={1.5} />

      <div className="container-site relative">
        <motion.div className="mt-6 flex flex-wrap gap-3 sm:mt-8" {...fade(1.9)}>
          <Link to="/founders" className="btn-primary px-7">
            Pitch us <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <a href="#portfolio" onClick={toPortfolio} className="btn-ghost px-7">
            Our portfolio
          </a>
        </motion.div>
      </div>

      <motion.div className="absolute inset-x-0 bottom-6 flex justify-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: reduce ? 0 : 2.4 }} aria-hidden="true">
        <motion.span className="grid h-10 w-10 place-items-center rounded-full border border-white/10 text-slate" animate={reduce ? undefined : { y: [0, 6, 0] }} transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}>
          <ArrowDown className="h-4 w-4" />
        </motion.span>
      </motion.div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 2. The problem                                                      */
/* ------------------------------------------------------------------ */

const SECTOR_ICONS: Record<string, LucideIcon> = { Energy: Zap, Manufacturing: Factory, Healthcare: HeartPulse, Finance: Landmark };

function Problem() {
  return (
    <section className="py-24 sm:py-32" aria-labelledby="problem-title">
      <div className="container-site">
        <SectionHeading
          id="problem-title"
          eyebrow="The problem"
          title="Most AI investors chase the next big model."
          intro="The real opportunity is getting AI to work inside the industries that run the world."
        />
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {sectors.map((s, i) => (
            <Reveal key={s.name} delay={i * 0.08}>
              <FlipTile name={s.name} line={s.line} Icon={SECTOR_ICONS[s.name]} index={i} />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function FlipTile({ name, line, Icon, index }: { name: string; line: string; Icon: LucideIcon; index: number }) {
  const reduce = useReducedMotion();
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false);
  const flipped = hovered || pinned;

  const face = 'absolute inset-0 flex flex-col rounded-2xl border p-6 backface-hidden';

  return (
    <button
      type="button"
      onPointerEnter={(e) => e.pointerType === 'mouse' && setHovered(true)}
      onPointerLeave={(e) => e.pointerType === 'mouse' && setHovered(false)}
      onClick={() => setPinned((p) => !p)}
      aria-pressed={pinned}
      className="perspective group relative block h-64 w-full rounded-2xl text-left"
    >
      <span className="sr-only">{name}: {line}</span>
      <motion.span
        aria-hidden="true"
        className="preserve-3d relative block h-full w-full"
        animate={reduce ? undefined : { rotateY: flipped ? 180 : 0 }}
        transition={{ type: 'spring', stiffness: 160, damping: 20 }}
      >
        <span className={cn(face, 'border-white/[0.08] bg-navy-800/80 transition-opacity', reduce && flipped && 'opacity-0')}>
          <span className="grid h-12 w-12 place-items-center rounded-xl border border-amber/30 bg-amber/10 text-amber">
            <Icon className="h-6 w-6" />
          </span>
          <span className="mt-auto font-display text-xs font-semibold tracking-[0.16em] text-slate">0{index + 1}</span>
          <span className="mt-1 font-display text-2xl font-semibold text-paper">{name}</span>
          <span className="mt-3 inline-flex items-center gap-1.5 text-sm text-slate">
            <span className="hidden [@media(hover:hover)]:inline">Hover</span>
            <span className="[@media(hover:hover)]:hidden">Tap</span> to see where AI helps
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </span>
        </span>
        <span
          className={cn(face, 'border-amber/40 bg-gradient-to-br from-navy-700 to-navy-800', reduce ? (flipped ? 'opacity-100' : 'opacity-0') : '[transform:rotateY(180deg)]', 'transition-opacity')}
        >
          <span className="h-px w-10 bg-amber shadow-glow" />
          <span className="mt-4 font-display text-sm font-semibold uppercase tracking-[0.14em] text-amber">{name}</span>
          <span className="mt-3 text-lg leading-snug text-paper">{line}</span>
        </span>
      </motion.span>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* 3. Our edge                                                         */
/* ------------------------------------------------------------------ */

const EDGE = [
  { Icon: HardHat, title: 'Operators, not spectators', line: 'We have built and sold software into these industries ourselves.' },
  { Icon: Handshake, title: 'We know how industries buy', line: 'We know who signs off, how long it takes, and what makes a pilot turn into a contract.' },
  { Icon: Rocket, title: 'Active from day one', line: 'We help with hiring, sales and new markets from the first week, not just at board meetings.' },
];

function Edge() {
  return (
    <section className="py-24 sm:py-32" aria-labelledby="edge-title">
      <div className="container-site">
        <SectionHeading id="edge-title" eyebrow="Our edge" title="We have done the job we are backing you to do." />
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {EDGE.map(({ Icon, title, line }, i) => (
            <Reveal key={title} delay={i * 0.1} className="h-full">
              <article className="card group relative h-full overflow-hidden p-8 transition duration-300 hover:-translate-y-1 hover:border-amber/30">
                <span className="absolute inset-x-8 top-0 h-px origin-left scale-x-[0.2] bg-amber shadow-glow transition-transform duration-500 group-hover:scale-x-100" aria-hidden="true" />
                <span className="grid h-12 w-12 place-items-center rounded-xl bg-white/[0.04] text-amber ring-1 ring-white/10">
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </span>
                <h3 className="mt-8 text-xl font-semibold text-paper">{title}</h3>
                <p className="mt-3 leading-relaxed text-slate-light">{line}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 4. By the numbers                                                   */
/* ------------------------------------------------------------------ */

function Numbers() {
  const stats: { value: React.ReactNode; label: string; note?: string }[] = [
    { value: <CountUp to={250} prefix="$" suffix="M" />, label: 'Fund I' },
    { value: <CountUp to={247} prefix="$" suffix="M" />, label: 'Committed by LPs' },
    { value: <CountUp to={8} />, label: 'Portfolio companies' },
    { value: <CountUp to={3} />, label: 'Markets', note: 'US, Asia, Europe' },
    { value: <><CountUp to={10} />–<CountUp to={15} suffix="%" /></>, label: 'Target ownership' },
    { value: <CountUp to={10} suffix="x" />, label: 'First exit', note: 'NoxTech' },
  ];
  return (
    <section className="relative py-24 sm:py-32" aria-labelledby="numbers-title">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-navy-800/50 to-transparent" aria-hidden="true" />
      <div className="container-site relative">
        <SectionHeading id="numbers-title" eyebrow="By the numbers" title="Fund I at a glance." />
        <dl className="mt-14 grid grid-cols-2 gap-px overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.08] lg:grid-cols-3">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={(i % 3) * 0.08} className="flex flex-col bg-navy p-6 sm:p-10">
              <dt className="order-2 mt-5 text-sm font-medium text-slate-light sm:text-base">
                {s.label}
                {s.note && <span className="mt-0.5 block text-slate">{s.note}</span>}
              </dt>
              <dd className="order-1 font-display text-4xl font-semibold text-paper sm:text-6xl">
                <Underline delay={0.4 + (i % 3) * 0.1}>{s.value}</Underline>
              </dd>
            </Reveal>
          ))}
        </dl>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 5. How we invest                                                    */
/* ------------------------------------------------------------------ */

function Process() {
  const [active, setActive] = useState(0);
  const reduce = useReducedMotion();
  const progress = active / (steps.length - 1);

  return (
    <section className="py-24 sm:py-32" aria-labelledby="process-title">
      <div className="container-site">
        <SectionHeading id="process-title" eyebrow="How we invest" title="Five steps, clearly explained." intro="Select a step to see what happens." />

        {/* Desktop: horizontal timeline */}
        <Reveal className="mt-16 hidden md:block">
          <div className="relative">
            <div className="absolute left-[10%] right-[10%] top-6 h-px bg-white/10" aria-hidden="true">
              <motion.div
                className="h-full origin-left bg-amber shadow-glow"
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: progress }}
                animate={{ scaleX: progress }}
                viewport={{ once: true }}
                transition={{ duration: reduce ? 0 : 0.6, ease: [0.65, 0, 0.35, 1] }}
              />
            </div>
            <ol className="relative grid grid-cols-5 gap-4">
              {steps.map((s, i) => {
                const isActive = i === active;
                const done = i <= active;
                return (
                  <li key={s.title} className="flex flex-col items-center text-center">
                    <button
                      type="button"
                      onClick={() => setActive(i)}
                      aria-expanded={isActive}
                      aria-controls={`step-panel-${i}`}
                      className="group flex flex-col items-center rounded-2xl px-2 pb-2"
                    >
                      <span
                        className={cn(
                          'grid h-12 w-12 place-items-center rounded-full border font-display text-sm font-semibold transition-all duration-300',
                          done ? 'border-amber bg-amber text-navy shadow-glow' : 'border-white/20 bg-navy text-slate group-hover:border-amber/60 group-hover:text-paper',
                          isActive && 'scale-110',
                        )}
                      >
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className={cn('mt-4 font-display text-lg font-semibold transition-colors', isActive ? 'text-paper' : 'text-slate-light group-hover:text-paper')}>{s.title}</span>
                    </button>
                    <AnimatePresence initial={false}>
                      {isActive && (
                        <motion.p
                          id={`step-panel-${i}`}
                          key="panel"
                          className="max-w-[220px] overflow-hidden text-sm leading-relaxed text-slate-light"
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: reduce ? 0 : 0.3 }}
                        >
                          <span className="block pt-2">{s.line}</span>
                        </motion.p>
                      )}
                    </AnimatePresence>
                  </li>
                );
              })}
            </ol>
          </div>
        </Reveal>

        {/* Mobile: vertical timeline */}
        <ol className="relative mt-12 md:hidden">
          <span className="absolute bottom-6 left-6 top-6 w-px bg-white/10" aria-hidden="true">
            <motion.span className="block h-full w-full origin-top bg-amber shadow-glow" animate={{ scaleY: progress }} transition={{ duration: reduce ? 0 : 0.5 }} />
          </span>
          {steps.map((s, i) => {
            const isActive = i === active;
            const done = i <= active;
            return (
              <li key={s.title} className="relative pb-3">
                <button type="button" onClick={() => setActive(i)} aria-expanded={isActive} aria-controls={`step-panel-m-${i}`} className="flex w-full items-center gap-4 rounded-2xl py-2 text-left">
                  <span className={cn('relative grid h-12 w-12 shrink-0 place-items-center rounded-full border font-display text-sm font-semibold transition', done ? 'border-amber bg-amber text-navy' : 'border-white/20 bg-navy text-slate')}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className={cn('font-display text-lg font-semibold', isActive ? 'text-paper' : 'text-slate-light')}>{s.title}</span>
                </button>
                <AnimatePresence initial={false}>
                  {isActive && (
                    <motion.p id={`step-panel-m-${i}`} className="overflow-hidden pl-16 text-slate-light" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: reduce ? 0 : 0.3 }}>
                      <span className="block pb-2">{s.line}</span>
                    </motion.p>
                  )}
                </AnimatePresence>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 6. Portfolio preview carousel                                       */
/* ------------------------------------------------------------------ */

function useVisibleCount() {
  const get = () => (typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches ? 2 : 1);
  const [n, setN] = useState(get);
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 768px)');
    const on = () => setN(mq.matches ? 2 : 1);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return n;
}

function PortfolioPreview() {
  const featured = companies.filter((c) => c.featured);
  const visible = useVisibleCount();
  const maxIndex = Math.max(0, featured.length - visible);
  const [index, setIndex] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => setIndex((i) => Math.min(i, maxIndex)), [maxIndex]);

  const go = (d: number) => setIndex((i) => Math.min(maxIndex, Math.max(0, i + d)));
  const onDragEnd = (_: unknown, info: PanInfo) => {
    if (info.offset.x < -60 || info.velocity.x < -400) go(1);
    else if (info.offset.x > 60 || info.velocity.x > 400) go(-1);
  };

  return (
    <section id="portfolio" tabIndex={-1} className="scroll-mt-20 py-24 outline-none sm:py-32" aria-labelledby="portfolio-title">
      <div className="container-site">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <SectionHeading id="portfolio-title" eyebrow="Portfolio" title="Some of the companies we back." />
          <Reveal className="flex items-center gap-2">
            <button type="button" onClick={() => go(-1)} disabled={index === 0} className="grid h-12 w-12 place-items-center rounded-full border border-white/15 text-paper transition hover:border-amber/60 disabled:cursor-not-allowed disabled:opacity-30" aria-label="Previous companies">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button type="button" onClick={() => go(1)} disabled={index === maxIndex} className="grid h-12 w-12 place-items-center rounded-full border border-white/15 text-paper transition hover:border-amber/60 disabled:cursor-not-allowed disabled:opacity-30" aria-label="Next companies">
              <ChevronRight className="h-5 w-5" />
            </button>
          </Reveal>
        </div>

        <Reveal className="mt-12">
          <div className="-mx-2 overflow-hidden" role="region" aria-roledescription="carousel" aria-label="Featured portfolio companies">
            <motion.ul
              className="flex cursor-grab touch-pan-y active:cursor-grabbing"
              animate={{ x: `-${(index * 100) / visible}%` }}
              transition={reduce ? { duration: 0 } : { type: 'spring', stiffness: 260, damping: 34 }}
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.15}
              onDragEnd={onDragEnd}
              aria-live="polite"
            >
              {featured.map((c, i) => {
                const shown = i >= index && i < index + visible;
                return (
                  <li key={c.slug} className="shrink-0 px-2" style={{ width: `${100 / visible}%` }} aria-roledescription="slide" aria-label={`${i + 1} of ${featured.length}`} aria-hidden={!shown}>
                    <Link
                      to={`/portfolio?company=${c.slug}`}
                      tabIndex={shown ? 0 : -1}
                      draggable={false}
                      className="card group relative flex h-full min-h-[300px] flex-col overflow-hidden p-8 transition duration-300 hover:border-amber/30 sm:p-10"
                    >
                      <span className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-amber/[0.05] blur-2xl transition group-hover:bg-amber/[0.1]" aria-hidden="true" />
                      <div className="flex items-center justify-between">
                        <Monogram name={c.name} size="lg" />
                        <StatusPill status={c.status} outcome={c.outcome} />
                      </div>
                      <h3 className="mt-8 text-2xl font-semibold text-paper sm:text-3xl">{c.name}</h3>
                      <p className="mt-3 max-w-md text-slate-light">{c.oneLiner}</p>
                      <div className="mt-auto flex flex-wrap items-center gap-x-5 gap-y-2 pt-8 text-sm text-slate">
                        <span>{c.sector}</span>
                        <span aria-hidden="true">·</span>
                        <span>{c.region}</span>
                        <span className="ml-auto inline-flex items-center gap-1 font-medium text-paper transition group-hover:text-amber">
                          View <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden="true" />
                        </span>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </motion.ul>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-between gap-6">
            <div className="flex gap-2" role="group" aria-label="Choose slide">
              {Array.from({ length: maxIndex + 1 }, (_, i) => (
                <button key={i} type="button" onClick={() => setIndex(i)} aria-label={`Go to slide ${i + 1}`} aria-current={i === index} className="grid h-8 w-8 place-items-center rounded-full">
                  <span className={cn('h-1.5 rounded-full transition-all duration-300', i === index ? 'w-7 bg-amber shadow-glow' : 'w-1.5 bg-white/25 hover:bg-white/50')} />
                </button>
              ))}
            </div>
            <Link to="/portfolio" className="btn-ghost">
              See all companies <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 7. Team preview                                                     */
/* ------------------------------------------------------------------ */

function TeamPreview() {
  return (
    <section className="py-24 sm:py-32" aria-labelledby="team-title">
      <div className="container-site">
        <div className="card relative overflow-hidden p-8 sm:p-12 lg:p-16">
          <div className="absolute inset-0 bg-grid opacity-60 [mask-image:linear-gradient(to_left,black,transparent_70%)]" aria-hidden="true" />
          <div className="relative grid items-center gap-10 lg:grid-cols-[1fr_auto]">
            <SectionHeading id="team-title" eyebrow="Team" title="A small team of operators." intro="People who have built, sold and run software in the industries we invest in." />
            <Reveal delay={0.15}>
              <ul className="flex flex-wrap items-start gap-x-3 gap-y-6 sm:gap-x-4 lg:justify-end" aria-label="Team members">
                {team.map((p, i) => (
                  <motion.li key={p.slug} className="group flex w-16 flex-col items-center" initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.2 + i * 0.07 }}>
                    <span className="rounded-full ring-4 ring-navy-800 transition-transform duration-300 group-hover:-translate-y-1.5">
                      <Avatar name={p.name} size="md" />
                    </span>
                    <span className="mt-3 text-sm font-medium text-slate-light">{p.name}</span>
                  </motion.li>
                ))}
                <li className="flex w-16 flex-col items-center text-center">
                  <span className="grid h-16 w-16 place-items-center rounded-full border border-dashed border-white/25 bg-navy-800 text-slate ring-4 ring-navy-800">
                    <Plus className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="mt-3 text-sm font-medium leading-tight text-slate">Joining soon</span>
                </li>
              </ul>
              <div className="mt-10 lg:text-right">
                <Link to="/team" className="btn-primary">
                  Meet the team <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/* 8. CTA band                                                         */
/* ------------------------------------------------------------------ */

function CtaBand() {
  return (
    <section className="relative overflow-hidden py-24 sm:py-32" aria-labelledby="cta-title">
      <div className="absolute inset-x-0 top-1/2 h-[360px] -translate-y-1/2 bg-amber/[0.07] blur-3xl" aria-hidden="true" />
      <div className="container-site relative text-center">
        <Reveal>
          <h2 id="cta-title" className="mx-auto max-w-3xl text-balance text-4xl font-bold leading-[1.05] text-paper sm:text-6xl">
            Building AI for a real industry? <Underline className="text-amber">Let’s talk.</Underline>
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-slate-light">Send us a short pitch. It takes about five minutes.</p>
          <Link to="/founders" className="btn-primary mt-10 px-8 text-base">
            Pitch us <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
