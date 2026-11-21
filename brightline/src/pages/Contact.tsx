import { useReducedMotion } from 'framer-motion';
import { ArrowRight, Mail, MapPin, Rocket, Users } from 'lucide-react';
import { useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { TextArea, TextField } from '../components/Field';
import { usePageTitle } from '../components/Layout';
import { PageHeader } from '../components/PageHeader';
import { Reveal } from '../components/Reveal';
import { useToast } from '../components/Toast';
import { CONTACT_EMAIL, OFFICE } from '../data';
import { saveSubmission } from '../lib/storage';
import { focusField, useForm } from '../lib/useForm';
import { email, maxLength, minLength, required, type Schema } from '../lib/validation';

type F = 'name' | 'email' | 'subject' | 'message';
const INITIAL: Record<F, string> = { name: '', email: '', subject: '', message: '' };
const SCHEMA: Schema<F> = {
  name: [required('Please enter your name.'), minLength(2, 'Please enter your full name.')],
  email: [required('Please enter your email.'), email],
  subject: [required('Please add a subject.'), maxLength(120)],
  message: [required('Please write a message.'), minLength(20, 'Please add a little more detail (at least 20 characters).')],
};

export default function Contact() {
  usePageTitle('Contact');
  const toast = useToast();
  const reduce = useReducedMotion();
  const { values, bind, check, reset } = useForm<F>(useMemo(() => INITIAL, []), useMemo(() => SCHEMA, []));
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const bad = check();
    if (bad) return focusField('contact-form', bad);
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, reduce ? 0 : 500));
    const saved = saveSubmission('messages', values, 'MSG');
    setSubmitting(false);
    reset();
    toast({ title: 'Message sent', body: `Thanks, ${values.name.split(' ')[0]}. Your reference is ${saved.reference}.` });
  };

  return (
    <>
      <PageHeader eyebrow="Contact" title="Let’s talk." intro="Founders, investors, partners and press are all welcome. Send a message, or email us directly." />

      <section className="container-site grid gap-10 pb-28 pt-12 lg:grid-cols-[1fr_1.4fr] lg:gap-16" aria-label="Contact details and form">
        <div className="space-y-4">
          <Reveal>
            <a href={`mailto:${CONTACT_EMAIL}`} className="card group flex items-start gap-4 p-6 transition hover:border-amber/30">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-amber/10 text-amber ring-1 ring-amber/25"><Mail className="h-5 w-5" aria-hidden="true" /></span>
              <span>
                <span className="block text-sm text-slate">Email</span>
                <span className="mt-0.5 block break-all font-display text-lg font-semibold text-paper group-hover:text-amber">{CONTACT_EMAIL}</span>
              </span>
            </a>
          </Reveal>
          <Reveal delay={0.06}>
            <div className="card flex items-start gap-4 p-6">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-amber/10 text-amber ring-1 ring-amber/25"><MapPin className="h-5 w-5" aria-hidden="true" /></span>
              <address className="not-italic">
                <span className="block text-sm text-slate">Office</span>
                <span className="mt-0.5 block font-display text-lg font-semibold text-paper">{OFFICE.line1}</span>
                <span className="block text-slate-light">{OFFICE.line2}</span>
              </address>
            </div>
          </Reveal>
          <Reveal delay={0.12}>
            <div className="card p-6">
              <p className="text-sm font-semibold uppercase tracking-wider text-slate">Looking for something specific?</p>
              <ul className="mt-4 space-y-2">
                <li>
                  <Link to="/founders" className="group flex min-h-[44px] items-center justify-between gap-3 rounded-xl px-3 text-paper hover:bg-white/[0.04]">
                    <span className="inline-flex items-center gap-3"><Rocket className="h-4 w-4 text-amber" aria-hidden="true" /> Founders: send a pitch</span>
                    <ArrowRight className="h-4 w-4 text-slate transition group-hover:translate-x-0.5 group-hover:text-amber" aria-hidden="true" />
                  </Link>
                </li>
                <li>
                  <Link to="/investors#request" className="group flex min-h-[44px] items-center justify-between gap-3 rounded-xl px-3 text-paper hover:bg-white/[0.04]">
                    <span className="inline-flex items-center gap-3"><Users className="h-4 w-4 text-amber" aria-hidden="true" /> Investors: request LP information</span>
                    <ArrowRight className="h-4 w-4 text-slate transition group-hover:translate-x-0.5 group-hover:text-amber" aria-hidden="true" />
                  </Link>
                </li>
              </ul>
            </div>
          </Reveal>
        </div>

        <Reveal delay={0.1}>
          <div className="card relative overflow-hidden p-6 sm:p-10">
            <span className="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-amber to-transparent" aria-hidden="true" />
            <h2 className="font-display text-2xl font-semibold text-paper">Send a message</h2>
            <p className="mt-1 text-slate-light">All fields are required.</p>
            <form id="contact-form" noValidate onSubmit={onSubmit} className="mt-8 grid gap-5 sm:grid-cols-2" aria-label="Contact form">
              <TextField label="Name" autoComplete="name" {...bind('name')} />
              <TextField label="Email" type="email" autoComplete="email" inputMode="email" {...bind('email')} />
              <TextField className="sm:col-span-2" label="Subject" {...bind('subject')} />
              <TextArea className="sm:col-span-2" label="Message" rows={6} {...bind('message')} />
              <div className="sm:col-span-2">
                <button type="submit" className="btn-primary w-full sm:w-auto" disabled={submitting}>
                  {submitting ? 'Sending…' : <>Send message <ArrowRight className="h-4 w-4" aria-hidden="true" /></>}
                </button>
              </div>
            </form>
          </div>
        </Reveal>
      </section>
    </>
  );
}
