import { AnimatePresence, LayoutGroup, motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import { useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { usePageTitle } from '../components/Layout';
import { Modal } from '../components/Modal';
import { Monogram } from '../components/Monogram';
import { PageHeader } from '../components/PageHeader';
import { StatusPill } from '../components/StatusPill';
import { companies, sectorGroups, type Company } from '../data';
import { cn } from '../lib/utils';

const STATUS = ['All', 'Active', 'Exited'] as const;
type StatusFilter = (typeof STATUS)[number];

export default function Portfolio() {
  usePageTitle('Portfolio');
  const reduce = useReducedMotion();
  const [params, setParams] = useSearchParams();

  // Filters and the open company live in the URL, so every view can be linked to and the back button works.
  const status = (STATUS.find((s) => s.toLowerCase() === params.get('status')) ?? 'All') as StatusFilter;
  const sector = sectorGroups.find((s) => s === params.get('sector')) ?? null;
  const openSlug = params.get('company');
  const open = companies.find((c) => c.slug === openSlug) ?? null;

  const update = (patch: Record<string, string | null>, replace = true) => {
    const next = new URLSearchParams(params);
    Object.entries(patch).forEach(([k, v]) => (v === null ? next.delete(k) : next.set(k, v)));
    setParams(next, { replace, preventScrollReset: true });
  };

  const list = useMemo(
    () => companies.filter((c) => (status === 'All' || c.status === status) && (!sector || c.sectorGroup === sector)),
    [status, sector],
  );

  const counts = useMemo(() => ({ All: companies.length, Active: companies.filter((c) => c.status === 'Active').length, Exited: companies.filter((c) => c.status === 'Exited').length }), []);

  return (
    <>
      <PageHeader eyebrow="Portfolio" title="Companies putting AI to work in real industries." intro="Eight companies across life sciences, climate, finance, manufacturing and software, in Europe, Africa, Asia and the Middle East." />

      <section className="container-site pb-28 pt-12" aria-label="Portfolio companies">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <LayoutGroup id="status">
            <div className="inline-flex self-start rounded-full border border-white/10 bg-navy-800/70 p-1" role="group" aria-label="Filter by status">
              {STATUS.map((s) => (
                <button
                  key={s}
                  type="button"
                  aria-pressed={status === s}
                  onClick={() => update({ status: s === 'All' ? null : s.toLowerCase() })}
                  className={cn('relative min-h-[40px] rounded-full px-5 text-sm font-medium transition-colors', status === s ? 'text-navy' : 'text-slate-light hover:text-paper')}
                >
                  {status === s && <motion.span layoutId="status-pill" className="absolute inset-0 rounded-full bg-amber" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />}
                  <span className="relative">{s} <span className="opacity-60">{counts[s]}</span></span>
                </button>
              ))}
            </div>
          </LayoutGroup>

          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by sector">
            <Chip active={!sector} onClick={() => update({ sector: null })}>All sectors</Chip>
            {sectorGroups.map((g) => (
              <Chip key={g} active={sector === g} onClick={() => update({ sector: sector === g ? null : g })}>{g}</Chip>
            ))}
          </div>
        </div>

        <p className="mt-6 text-sm text-slate" aria-live="polite">
          Showing {list.length} of {companies.length} companies
        </p>

        <motion.ul layout={!reduce} className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <AnimatePresence mode="popLayout" initial={false}>
            {list.map((c) => (
              <motion.li
                key={c.slug}
                layout={!reduce}
                initial={{ opacity: 0, scale: reduce ? 1 : 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: reduce ? 1 : 0.94 }}
                transition={{ duration: reduce ? 0.1 : 0.3 }}
              >
                <CompanyCard company={c} onOpen={() => update({ company: c.slug }, false)} />
              </motion.li>
            ))}
          </AnimatePresence>
        </motion.ul>

        {list.length === 0 && (
          <div className="card mt-6 flex flex-col items-center p-12 text-center">
            <p className="text-lg text-paper">No companies match these filters.</p>
            <button type="button" onClick={() => update({ status: null, sector: null })} className="btn-ghost mt-6">Clear filters</button>
          </div>
        )}
      </section>

      <Modal open={!!open} onClose={() => update({ company: null })} title={open ? `${open.name} details` : 'Company details'}>
        {open && <CompanyDetail company={open} />}
      </Modal>
    </>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn('min-h-[38px] rounded-full border px-4 text-sm font-medium transition', active ? 'border-amber/60 bg-amber/10 text-amber' : 'border-white/10 text-slate-light hover:border-white/25 hover:text-paper')}
    >
      {children}
    </button>
  );
}

function CompanyCard({ company: c, onOpen }: { company: Company; onOpen: () => void }) {
  return (
    <button type="button" onClick={onOpen} className="card group relative flex h-full w-full flex-col overflow-hidden p-6 text-left transition duration-300 hover:-translate-y-1 hover:border-amber/30 hover:shadow-card" aria-haspopup="dialog" aria-label={`${c.name}: ${c.oneLiner} ${c.sectorGroup}, ${c.region}. ${c.status}${c.outcome ? `, ${c.outcome}` : ''}. View details`}>
      <span className="absolute inset-x-6 top-0 h-px origin-left scale-x-0 bg-amber shadow-glow transition-transform duration-500 group-hover:scale-x-100" aria-hidden="true" />
      <div className="flex items-start justify-between gap-3">
        <Monogram name={c.name} />
        <StatusPill status={c.status} outcome={c.outcome} />
      </div>
      <h2 className="mt-6 font-display text-xl font-semibold text-paper">{c.name}</h2>
      <p className="mt-2 text-[15px] leading-relaxed text-slate-light">{c.oneLiner}</p>
      <div className="mt-auto flex items-center justify-between pt-6 text-sm">
        <span className="text-slate">{c.sectorGroup} · {c.region}</span>
        <ArrowUpRight className="h-4 w-4 text-slate transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-amber" aria-hidden="true" />
      </div>
    </button>
  );
}

function CompanyDetail({ company: c }: { company: Company }) {
  const rows: [string, string][] = [
    ['Sector', c.sector],
    ['Region', c.region],
    ['Stage at investment', c.stage],
    ['Year invested', String(c.year)],
    ['Status', c.outcome ? `${c.status} (${c.outcome})` : c.status],
  ];
  return (
    <div className="p-7 sm:p-10">
      <Monogram name={c.name} size="lg" />
      <p className="mt-6 font-display text-3xl font-semibold text-paper" aria-hidden="true">{c.name}</p>
      <p className="mt-3 text-lg leading-relaxed text-slate-light">{c.oneLiner}</p>
      <dl className="mt-8 divide-y divide-white/[0.07] border-y border-white/[0.07]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-center justify-between gap-4 py-3.5">
            <dt className="text-sm text-slate">{k}</dt>
            <dd className="text-right font-medium text-paper">{k === 'Status' ? <StatusPill status={c.status} outcome={c.outcome} /> : v}</dd>
          </div>
        ))}
      </dl>
      <Link to="/founders" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-amber hover:text-amber-soft">
        Building something similar? Pitch us <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
    </div>
  );
}
