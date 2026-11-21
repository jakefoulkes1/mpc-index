import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, Pencil, Send } from 'lucide-react';
import { useMemo, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Underline } from '../components/BrightLine';
import { SelectField, TextArea, TextField } from '../components/Field';
import { usePageTitle } from '../components/Layout';
import { PageHeader } from '../components/PageHeader';
import { Reveal, SectionHeading } from '../components/Reveal';
import { SuccessPanel } from '../components/SuccessPanel';
import { saveSubmission } from '../lib/storage';
import { focusField, useForm } from '../lib/useForm';
import { email, maxLength, minLength, required, website, type Schema } from '../lib/validation';
import { cn } from '../lib/utils';

const LOOK_FOR = [
  { title: 'A real problem in a real industry', line: 'Work that is slow, costly or error-prone today in energy, manufacturing, healthcare or finance.' },
  { title: 'AI that does the work', line: 'Your product automates a task people do by hand, not just a dashboard on top.' },
  { title: 'Customers who pay', line: 'Revenue or paid pilots, and a clear reason why customers bought.' },
  { title: 'A team that knows the buyer', line: 'You understand how your customers make decisions and roll out new tools.' },
  { title: 'Series A or B', line: 'You are raising your first or second institutional round to grow.' },
  { title: 'Room to grow across markets', line: 'A business that can expand across the US, Asia and Europe.' },
];

const BRING = [
  { title: 'Sales into large buyers', line: 'Help with pricing, pilots and procurement, from first meeting to signed contract.' },
  { title: 'Introductions that matter', line: 'Customers, partners and senior hires in the industries we know.' },
  { title: 'New markets', line: 'Practical support when you expand into the US, Asia or Europe.' },
  { title: 'Money for later rounds', line: 'We keep capital in reserve to keep backing our best companies.' },
];

const SECTORS = ['Energy', 'Manufacturing', 'Healthcare', 'Finance', 'Other'] as const;
const STAGES = ['Pre-seed', 'Seed', 'Series A', 'Series B', 'Series C or later'] as const;

type Field = 'name' | 'email' | 'company' | 'website' | 'sector' | 'stage' | 'pitch';
const INITIAL: Record<Field, string> = { name: '', email: '', company: '', website: '', sector: '', stage: '', pitch: '' };
const SCHEMA: Schema<Field> = {
  name: [required('Please enter your name.'), minLength(2, 'Please enter your full name.')],
  email: [required('Please enter your email.'), email],
  company: [required('Please enter your company name.')],
  website: [required('Please enter your website.'), website],
  sector: [required('Please choose a sector.')],
  stage: [required('Please choose a stage.')],
  pitch: [required('Please add a one-line pitch.'), minLength(15, 'Please add a little more detail (at least 15 characters).'), maxLength(160)],
};
const STEP_FIELDS: Field[][] = [['name', 'email', 'company'], ['website', 'sector', 'stage', 'pitch'], []];
const STEP_LABELS = ['About you', 'Your company', 'Review'];

export default function Founders() {
  usePageTitle('For founders');
  return (
    <>
      <PageHeader eyebrow="For founders" title={<>Building AI for a real industry? <span className="text-amber">Pitch us.</span></>} intro="We back Series A and B companies using AI to automate how energy, manufacturing, healthcare and finance work. Here is what we look for and what we do after we invest.">
        <a href="#pitch" className="btn-primary" onClick={(e) => { e.preventDefault(); document.getElementById('pitch')?.scrollIntoView({ behavior: 'smooth' }); document.getElementById('pitch-form')?.querySelector<HTMLElement>('input')?.focus({ preventScroll: true }); }}>
          Start your pitch <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </a>
      </PageHeader>

      <section className="container-site grid gap-16 py-20 lg:grid-cols-2 lg:gap-20" aria-label="What we look for and what we bring">
        <div>
          <SectionHeading eyebrow="What we look for" title="Six signs we should talk." />
          <ul className="mt-10 space-y-3">
            {LOOK_FOR.map((item, i) => (
              <Reveal key={item.title} delay={i * 0.05}>
                <li className="card flex gap-4 p-5">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-amber text-navy" aria-hidden="true">
                    <Check className="h-4 w-4" strokeWidth={3} />
                  </span>
                  <div>
                    <p className="font-semibold text-paper">{item.title}</p>
                    <p className="mt-1 text-slate-light">{item.line}</p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ul>
        </div>
        <div>
          <SectionHeading eyebrow="What we bring" title="After we invest." />
          <ol className="mt-10 space-y-3">
            {BRING.map((item, i) => (
              <Reveal key={item.title} delay={i * 0.06}>
                <li className="card flex gap-5 p-5">
                  <span className="font-display text-2xl font-semibold text-amber" aria-hidden="true">0{i + 1}</span>
                  <div>
                    <p className="font-semibold text-paper">{item.title}</p>
                    <p className="mt-1 text-slate-light">{item.line}</p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ol>
          <Reveal className="mt-8 rounded-2xl border border-amber/25 bg-amber/[0.05] p-6">
            <p className="text-slate-light">
              We take <Underline className="font-semibold text-paper">10–15%</Underline> ownership and every decision goes through our investment committee. You will always know where you stand.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="pitch" className="scroll-mt-20 py-20 sm:py-28" aria-labelledby="pitch-title">
        <div className="container-site">
          <div className="mx-auto max-w-2xl">
            <SectionHeading id="pitch-title" eyebrow="Pitch us" title="Three short steps." intro="Tell us about you and your company. Every pitch is read by our team." />
            <Reveal className="mt-10">
              <PitchForm />
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}

function PitchForm() {
  const reduce = useReducedMotion();
  const schema = useMemo(() => SCHEMA, []);
  const initial = useMemo(() => INITIAL, []);
  const { values, bind, check, reset } = useForm<Field>(initial, schema);
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [reference, setReference] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const goTo = (n: number) => {
    setDir(n > step ? 1 : -1);
    setStep(n);
    window.setTimeout(() => {
      const el = cardRef.current?.querySelector<HTMLElement>(n === 2 ? '[data-step-heading]' : 'input, select, textarea');
      el?.focus();
    }, reduce ? 0 : 320);
  };

  const next = () => {
    const bad = check(STEP_FIELDS[step]);
    if (bad) {
      focusField('pitch-form', bad);
      return;
    }
    goTo(step + 1);
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (step < 2) return next();
    const bad = check();
    if (bad) {
      // Send the user back to the step with the problem.
      const s = STEP_FIELDS.findIndex((f) => f.includes(bad));
      goTo(s);
      return;
    }
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, reduce ? 0 : 700));
    const saved = saveSubmission('pitches', { ...values, website: values.website.trim() }, 'BLV');
    setSubmitting(false);
    setReference(saved.reference);
  };

  const startOver = () => {
    reset();
    setReference(null);
    setStep(0);
  };

  const progress = reference ? 1 : (step + 1) / 3;
  const stageNote = values.stage && !['Series A', 'Series B'].includes(values.stage);

  return (
    <div ref={cardRef} className="card relative overflow-hidden">
      {/* Progress */}
      <div className="border-b border-white/[0.07] px-6 pb-5 pt-6 sm:px-10">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-paper">{reference ? 'Submitted' : `Step ${step + 1} of 3: ${STEP_LABELS[step]}`}</span>
          <span className="text-slate">{Math.round(progress * 100)}%</span>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.07]" role="progressbar" aria-label="Pitch form progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)}>
          <motion.div className="h-full rounded-full bg-amber shadow-glow" initial={false} animate={{ width: `${progress * 100}%` }} transition={{ duration: reduce ? 0 : 0.5, ease: [0.65, 0, 0.35, 1] }} />
        </div>
        <ol className="mt-4 hidden grid-cols-3 gap-2 text-xs sm:grid">
          {STEP_LABELS.map((l, i) => (
            <li key={l} className={cn('flex items-center gap-2', i <= step || reference ? 'text-paper' : 'text-slate')}>
              <span className={cn('grid h-5 w-5 place-items-center rounded-full text-[10px] font-semibold', i < step || reference ? 'bg-amber text-navy' : i === step ? 'border border-amber text-amber' : 'border border-white/20')}>
                {i < step || reference ? <Check className="h-3 w-3" strokeWidth={3} aria-hidden="true" /> : i + 1}
              </span>
              {l}
            </li>
          ))}
        </ol>
      </div>

      <div className="px-6 py-8 sm:px-10 sm:py-10">
        {reference ? (
          <SuccessPanel
            title="Pitch received"
            reference={reference}
            body={<p>Thanks, {values.name.split(' ')[0] || 'there'}. Your pitch for {values.company} has been saved. Keep your reference number. Please quote it if you contact us about this pitch.</p>}
          >
            <button type="button" className="btn-ghost" onClick={startOver}>Submit another pitch</button>
            <Link to="/portfolio" className="btn-primary">See our portfolio <ArrowRight className="h-4 w-4" aria-hidden="true" /></Link>
          </SuccessPanel>
        ) : (
          <form id="pitch-form" noValidate onSubmit={onSubmit} aria-label="Pitch form">
            <AnimatePresence mode="wait" custom={dir} initial={false}>
              <motion.div
                key={step}
                custom={dir}
                initial={reduce ? { opacity: 0 } : { opacity: 0, x: 40 * dir }}
                animate={{ opacity: 1, x: 0 }}
                exit={reduce ? { opacity: 0 } : { opacity: 0, x: -40 * dir }}
                transition={{ duration: reduce ? 0.1 : 0.28, ease: [0.22, 1, 0.36, 1] }}
              >
                {step === 0 && (
                  <fieldset className="grid gap-5">
                    <legend className="sr-only">About you</legend>
                    <TextField label="Your name" autoComplete="name" {...bind('name')} />
                    <TextField label="Email" type="email" autoComplete="email" inputMode="email" {...bind('email')} />
                    <TextField label="Company" autoComplete="organization" {...bind('company')} />
                  </fieldset>
                )}
                {step === 1 && (
                  <fieldset className="grid gap-5 sm:grid-cols-2">
                    <legend className="sr-only">Your company</legend>
                    <TextField className="sm:col-span-2" label="Website" inputMode="url" autoComplete="url" placeholder="company.com" {...bind('website')} />
                    <SelectField label="Sector" placeholder="Choose a sector" options={SECTORS} {...bind('sector')} />
                    <SelectField label="Stage" placeholder="Choose a stage" options={STAGES} hint={stageNote ? 'We mainly invest at Series A and B, but you are still welcome to send your pitch.' : undefined} {...bind('stage')} />
                    <TextArea
                      className="sm:col-span-2"
                      label="One-line pitch"
                      rows={3}
                      maxLength={160}
                      placeholder="We use AI to…"
                      hint={`${values.pitch.length}/160 characters`}
                      {...bind('pitch')}
                    />
                  </fieldset>
                )}
                {step === 2 && (
                  <div>
                    <h3 data-step-heading tabIndex={-1} className="font-display text-xl font-semibold text-paper outline-none">Check your details</h3>
                    <p className="mt-1 text-slate-light">Make any changes, then send your pitch.</p>
                    <ReviewGroup title="About you" onEdit={() => goTo(0)} rows={[['Name', values.name], ['Email', values.email], ['Company', values.company]]} />
                    <ReviewGroup title="Your company" onEdit={() => goTo(1)} rows={[['Website', values.website], ['Sector', values.sector], ['Stage', values.stage], ['Pitch', values.pitch]]} />
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

            <div className="mt-10 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
              {step > 0 ? (
                <button type="button" onClick={() => goTo(step - 1)} className="btn-ghost">
                  <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back
                </button>
              ) : (
                <span className="hidden sm:block" />
              )}
              {step < 2 ? (
                <button type="submit" className="btn-primary">
                  Continue <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </button>
              ) : (
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? (
                    <>
                      <motion.span className="h-4 w-4 rounded-full border-2 border-navy/30 border-t-navy" animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }} aria-hidden="true" />
                      Sending…
                    </>
                  ) : (
                    <>
                      Send pitch <Send className="h-4 w-4" aria-hidden="true" />
                    </>
                  )}
                </button>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function ReviewGroup({ title, rows, onEdit }: { title: string; rows: [string, string][]; onEdit: () => void }) {
  return (
    <div className="mt-6 rounded-2xl border border-white/[0.08] bg-navy-900/50">
      <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3">
        <p className="text-sm font-semibold uppercase tracking-wider text-slate">{title}</p>
        <button type="button" onClick={onEdit} className="inline-flex min-h-[36px] items-center gap-1.5 rounded-full px-3 text-sm font-medium text-amber hover:bg-amber/10">
          <Pencil className="h-3.5 w-3.5" aria-hidden="true" /> Edit <span className="sr-only">{title}</span>
        </button>
      </div>
      <dl className="divide-y divide-white/[0.06]">
        {rows.map(([k, v]) => (
          <div key={k} className="grid gap-1 px-5 py-3 sm:grid-cols-[120px_1fr] sm:gap-4">
            <dt className="text-sm text-slate">{k}</dt>
            <dd className="break-words text-paper">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
