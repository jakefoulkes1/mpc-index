import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, CalendarClock, Layers, Percent, PiggyBank, Scale } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { Underline } from '../components/BrightLine';
import { Checkbox } from '../components/Checkbox';
import { SelectField, TextArea, TextField } from '../components/Field';
import { usePageTitle } from '../components/Layout';
import { PageHeader } from '../components/PageHeader';
import { Reveal, SectionHeading } from '../components/Reveal';
import { SuccessPanel } from '../components/SuccessPanel';
import { saveSubmission } from '../lib/storage';
import { focusField, useForm } from '../lib/useForm';
import { email, minLength, required, type Schema } from '../lib/validation';

const TERMS = [
  { Icon: Layers, label: 'European waterfall', title: 'You are paid back first', line: 'Profits are worked out across the whole fund, not deal by deal. We only share in profits after investors have their money back.' },
  { Icon: Percent, label: '8% hurdle', title: 'A minimum return before we share', line: 'Investors also receive an 8% yearly preferred return before the manager earns any share of profits.' },
  { Icon: PiggyBank, label: '2% fee', title: 'A yearly fee to run the fund', line: 'A 2% annual management fee pays for the team, research and running the fund.' },
  { Icon: Scale, label: '20% carry', title: 'We earn when you earn', line: 'After the steps above, profits are split 80% to investors and 20% to the manager.' },
  { Icon: CalendarClock, label: 'Quarterly reporting', title: 'Clear updates, every quarter', line: 'A written report each quarter on every company and the fund as a whole.' },
];

export default function Investors() {
  usePageTitle('For investors');
  return (
    <>
      <PageHeader
        eyebrow="For investors"
        title={<>A fund built so <span className="text-amber">investors are paid first.</span></>}
        intro="Brightline Ventures Fund I is a $250M fund. Our terms are standard and simple. Here is how they work, in plain English."
      >
        <a href="#request" className="btn-primary" onClick={(e) => { e.preventDefault(); document.getElementById('request')?.scrollIntoView({ behavior: 'smooth' }); }}>
          Request LP information <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </a>
      </PageHeader>

      <section className="container-site py-20" aria-labelledby="terms-title">
        <SectionHeading id="terms-title" eyebrow="Our approach" title="Five terms, explained." />
        <ul className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {TERMS.map(({ Icon, label, title, line }, i) => (
            <Reveal key={label} delay={(i % 3) * 0.08} className="h-full">
              <li className="card group h-full p-7 transition duration-300 hover:border-amber/30">
                <div className="flex items-center gap-3">
                  <span className="grid h-11 w-11 place-items-center rounded-xl bg-amber/10 text-amber ring-1 ring-amber/25">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="font-display text-sm font-semibold uppercase tracking-[0.14em] text-amber">{label}</span>
                </div>
                <h3 className="mt-6 text-xl font-semibold text-paper">{title}</h3>
                <p className="mt-2 leading-relaxed text-slate-light">{line}</p>
              </li>
            </Reveal>
          ))}
        </ul>
      </section>

      <section className="py-20 sm:py-28" aria-labelledby="flow-title">
        <div className="container-site grid items-center gap-14 lg:grid-cols-[1fr_1.15fr]">
          <div>
            <SectionHeading id="flow-title" eyebrow="How returns flow" title="Money comes back to investors first." />
            <Reveal delay={0.1}>
              <ol className="mt-8 space-y-5 text-slate-light">
                <li><span className="font-semibold text-paper">1. Capital back.</span> When companies are sold, investors get back all the money they put into the fund.</li>
                <li><span className="font-semibold text-paper">2. Preferred return.</span> Investors then receive an 8% yearly return on that money.</li>
                <li><span className="font-semibold text-paper">3. Profit split.</span> Only then are remaining profits shared: <Underline className="font-semibold text-paper">80%</Underline> to investors, <Underline className="font-semibold text-paper">20%</Underline> to the manager.</li>
              </ol>
              <p className="mt-8 text-sm text-slate">This is a simplified summary. The full terms are set out in the fund’s legal documents, which are shared with qualified investors on request.</p>
            </Reveal>
          </div>
          <Reveal delay={0.15}>
            <WaterfallDiagram />
          </Reveal>
        </div>
      </section>

      <section id="request" className="scroll-mt-20 py-20 sm:py-28" aria-labelledby="request-title">
        <div className="container-site">
          <div className="mx-auto max-w-2xl">
            <SectionHeading id="request-title" eyebrow="Limited partners" title="Request LP information." intro="Tell us a little about yourself and we will share fund materials with qualified investors." />
            <Reveal className="mt-10">
              <LpForm />
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}

function WaterfallDiagram() {
  const reduce = useReducedMotion();
  const tiers = [
    { n: '01', title: 'Return of capital', who: '100% to investors', lp: 100 },
    { n: '02', title: '8% preferred return', who: '100% to investors', lp: 100 },
    { n: '03', title: 'Remaining profit', who: '80% investors · 20% manager', lp: 80 },
  ];
  return (
    <figure className="card relative overflow-hidden p-6 sm:p-8" aria-labelledby="waterfall-caption">
      <figcaption id="waterfall-caption" className="sr-only">
        Diagram: fund proceeds flow first to return investors’ capital, then to an 8% preferred return for investors, then remaining profit is split 80% to investors and 20% to the manager.
      </figcaption>
      <div aria-hidden="true">
        <div className="flex items-center justify-between rounded-2xl border border-amber/30 bg-amber/[0.06] px-5 py-4">
          <span className="font-display font-semibold text-paper">Money returned from exits</span>
          <span className="h-2.5 w-2.5 rounded-full bg-amber shadow-glow" />
        </div>
        {tiers.map((t, i) => (
          <div key={t.n}>
            <FlowConnector delay={i * 0.4} reduce={!!reduce} />
            <motion.div
              className="rounded-2xl border border-white/[0.08] bg-navy-900/60 p-5"
              initial={{ opacity: reduce ? 1 : 0.35 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, amount: 0.6 }}
              transition={{ delay: reduce ? 0 : 0.2 + i * 0.4, duration: 0.4 }}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-display font-semibold text-paper"><span className="mr-2 text-amber">{t.n}</span>{t.title}</p>
                <p className="text-sm text-slate-light">{t.who}</p>
              </div>
              <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-white/[0.06]">
                <motion.div
                  className="h-full bg-amber shadow-glow"
                  initial={{ width: reduce ? `${t.lp}%` : '0%' }}
                  whileInView={{ width: `${t.lp}%` }}
                  viewport={{ once: true, amount: 0.6 }}
                  transition={{ delay: reduce ? 0 : 0.3 + i * 0.4, duration: reduce ? 0 : 0.6, ease: [0.65, 0, 0.35, 1] }}
                />
                {t.lp < 100 && (
                  <motion.div
                    className="h-full bg-[#8FA8FF]"
                    initial={{ width: reduce ? `${100 - t.lp}%` : '0%' }}
                    whileInView={{ width: `${100 - t.lp}%` }}
                    viewport={{ once: true, amount: 0.6 }}
                    transition={{ delay: reduce ? 0 : 0.9 + i * 0.4, duration: reduce ? 0 : 0.4 }}
                  />
                )}
              </div>
            </motion.div>
          </div>
        ))}
        <div className="mt-6 flex flex-wrap gap-5 text-sm text-slate-light">
          <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-amber" /> Investors (LPs)</span>
          <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[#8FA8FF]" /> Manager (carry)</span>
        </div>
      </div>
    </figure>
  );
}

function FlowConnector({ delay, reduce }: { delay: number; reduce: boolean }) {
  return (
    <div className="relative mx-auto h-10 w-px bg-white/10">
      <motion.div
        className="absolute inset-0 origin-top bg-amber shadow-glow"
        initial={{ scaleY: reduce ? 1 : 0 }}
        whileInView={{ scaleY: 1 }}
        viewport={{ once: true }}
        transition={{ delay: reduce ? 0 : delay, duration: reduce ? 0 : 0.4 }}
      />
      {!reduce && (
        <motion.span
          className="absolute -left-[3px] h-[7px] w-[7px] rounded-full bg-amber shadow-glow"
          animate={{ top: ['-4px', '36px'], opacity: [0, 1, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, delay: delay + 0.8, ease: 'easeInOut' }}
        />
      )}
    </div>
  );
}

const INVESTOR_TYPES = ['Family office', 'Fund of funds', 'Endowment or foundation', 'Pension fund', 'Corporate', 'Individual investor', 'Other'] as const;
type LpField = 'name' | 'email' | 'organisation' | 'type' | 'message' | 'confirm';
const LP_INITIAL: Record<LpField, string> = { name: '', email: '', organisation: '', type: '', message: '', confirm: '' };
const LP_SCHEMA: Schema<LpField> = {
  name: [required('Please enter your name.'), minLength(2, 'Please enter your full name.')],
  email: [required('Please enter your email.'), email],
  organisation: [required('Please enter your organisation, or “Individual”.')],
  type: [required('Please choose an investor type.')],
  message: [],
  confirm: [required('Please confirm to continue.')],
};

function LpForm() {
  const reduce = useReducedMotion();
  const { values, errors, bind, check, reset, setField } = useForm<LpField>(useMemo(() => LP_INITIAL, []), useMemo(() => LP_SCHEMA, []));
  const [submitting, setSubmitting] = useState(false);
  const [reference, setReference] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const bad = check();
    if (bad) return focusField('lp-form', bad);
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, reduce ? 0 : 600));
    const saved = saveSubmission('lp-requests', values, 'LP');
    setSubmitting(false);
    setReference(saved.reference);
  };

  return (
    <div className="card relative overflow-hidden p-6 sm:p-10">
      <span className="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-amber to-transparent" aria-hidden="true" />
      {reference ? (
        <SuccessPanel title="Request received" reference={reference} body={<p>Thank you, {values.name.split(' ')[0]}. Your request has been saved. Please quote your reference if you follow up by email.</p>}>
          <button type="button" className="btn-ghost" onClick={() => { reset(); setReference(null); }}>Send another request</button>
        </SuccessPanel>
      ) : (
        <form id="lp-form" noValidate onSubmit={onSubmit} className="grid gap-5 sm:grid-cols-2" aria-label="Request LP information">
          <TextField label="Full name" autoComplete="name" {...bind('name')} />
          <TextField label="Email" type="email" autoComplete="email" inputMode="email" {...bind('email')} />
          <TextField label="Organisation" autoComplete="organization" {...bind('organisation')} />
          <SelectField label="Investor type" placeholder="Choose one" options={INVESTOR_TYPES} {...bind('type')} />
          <TextArea className="sm:col-span-2" label="Anything you would like to know?" optional rows={4} {...bind('message')} />
          <div className="sm:col-span-2">
            <Checkbox name="confirm" checked={values.confirm === 'yes'} onChange={(v) => setField('confirm', v ? 'yes' : '')} error={errors.confirm}>
              I confirm that I am a professional or accredited investor, or am asking on behalf of one. I understand this request is not an offer to sell securities.
            </Checkbox>
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary w-full sm:w-auto" disabled={submitting}>
              {submitting ? 'Sending…' : <>Request LP information <ArrowRight className="h-4 w-4" aria-hidden="true" /></>}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
