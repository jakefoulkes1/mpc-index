import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../components/Layout';
import { Modal } from '../components/Modal';
import { Avatar } from '../components/Monogram';
import { PageHeader } from '../components/PageHeader';
import { team, type Person } from '../data';

export default function Team() {
  usePageTitle('Team');
  const reduce = useReducedMotion();
  const [open, setOpen] = useState<Person | null>(null);

  return (
    <>
      <PageHeader eyebrow="Team" title="Operators who know how real industries work." intro="We have built and sold software into energy, manufacturing, healthcare and finance. Now we back the teams doing it next." />

      <section className="container-site pb-28 pt-12" aria-label="Team members">
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {team.map((p, i) => (
            <motion.li key={p.slug} initial={{ opacity: 0, y: reduce ? 0 : 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.5, delay: reduce ? 0 : (i % 3) * 0.08 }}>
              <button
                type="button"
                onClick={() => setOpen(p)}
                aria-haspopup="dialog"
                className="card group relative flex h-full w-full flex-col overflow-hidden p-8 text-left transition duration-300 hover:-translate-y-2 hover:border-amber/30 hover:shadow-card"
              >
                <span className="absolute inset-x-8 top-0 h-px origin-left scale-x-[0.15] bg-amber shadow-glow transition-transform duration-500 group-hover:scale-x-100" aria-hidden="true" />
                <Avatar name={p.name} size="lg" />
                <h2 className="mt-8 font-display text-2xl font-semibold text-paper">{p.name}</h2>
                <p className="mt-1 font-medium text-amber">{p.role}</p>
                <p className="mt-4 leading-relaxed text-slate-light">{p.summary}</p>
                <span className="mt-auto inline-flex items-center gap-1.5 pt-8 text-sm font-medium text-slate transition group-hover:text-paper">
                  Read bio <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                </span>
              </button>
            </motion.li>
          ))}
          <motion.li initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}>
            <div className="flex h-full min-h-[320px] flex-col rounded-2xl border border-dashed border-white/15 p-8">
              <Avatar name="" size="lg" muted />
              <h2 className="mt-8 font-display text-2xl font-semibold text-slate-light">Joining soon</h2>
              <p className="mt-4 leading-relaxed text-slate">A new member of the team will be introduced here.</p>
            </div>
          </motion.li>
        </ul>

        <div className="card mt-16 flex flex-col items-start justify-between gap-6 p-8 sm:flex-row sm:items-center sm:p-10">
          <div>
            <h2 className="font-display text-2xl font-semibold text-paper">Want to work with us?</h2>
            <p className="mt-2 text-slate-light">Founders, investors and partners can reach the team directly.</p>
          </div>
          <Link to="/contact" className="btn-primary shrink-0">Get in touch <ArrowRight className="h-4 w-4" aria-hidden="true" /></Link>
        </div>
      </section>

      <Modal open={!!open} onClose={() => setOpen(null)} title={open ? `${open.name}, ${open.role}` : 'Team member'}>
        {open && (
          <div className="p-7 sm:p-10">
            <Avatar name={open.name} size="lg" />
            <p className="mt-6 font-display text-3xl font-semibold text-paper" aria-hidden="true">{open.name}</p>
            <p className="mt-1 font-medium text-amber">{open.role}</p>
            <div className="mt-6 space-y-2 text-lg leading-relaxed text-slate-light">
              {open.bio.map((line) => <p key={line}>{line}</p>)}
            </div>
            <a href={open.linkedin} target="_blank" rel="noopener noreferrer" className="btn-ghost mt-8">
              LinkedIn <ExternalLink className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">(opens in a new tab)</span>
            </a>
          </div>
        )}
      </Modal>
    </>
  );
}
