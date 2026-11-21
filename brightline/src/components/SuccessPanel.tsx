import { motion, useReducedMotion } from 'framer-motion';
import { Copy, Check } from 'lucide-react';
import { useEffect, useRef, useState, type ReactNode } from 'react';

export function SuccessPanel({ title, body, reference, children }: { title: string; body: ReactNode; reference?: string; children?: ReactNode }) {
  const reduce = useReducedMotion();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    headingRef.current?.focus();
  }, []);

  const copy = async () => {
    if (!reference) return;
    try {
      await navigator.clipboard.writeText(reference);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may be blocked; the reference is still visible */
    }
  };

  const t = (delay: number) => ({ duration: reduce ? 0 : 0.6, delay: reduce ? 0 : delay, ease: [0.22, 1, 0.36, 1] as const });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center py-6 text-center">
      <div className="relative">
        <motion.span
          aria-hidden="true"
          className="absolute inset-0 rounded-full bg-amber/20 blur-2xl"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1.2 }}
          transition={t(0.2)}
        />
        <svg viewBox="0 0 96 96" className="relative h-24 w-24" aria-hidden="true">
          <motion.circle cx="48" cy="48" r="44" fill="none" stroke="#F2B33D" strokeWidth="2" pathLength={1} strokeDasharray="1 1" initial={{ strokeDashoffset: reduce ? 0 : 1 }} animate={{ strokeDashoffset: 0 }} transition={{ ...t(0), duration: reduce ? 0 : 0.8 }} />
          <motion.path d="M30 49 L43 62 L67 36" fill="none" stroke="#F2B33D" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" initial={{ strokeDashoffset: reduce ? 0 : 1 }} animate={{ strokeDashoffset: 0 }} transition={{ ...t(0.6), duration: reduce ? 0 : 0.5 }} />
        </svg>
      </div>
      <motion.h3 ref={headingRef} tabIndex={-1} className="mt-6 text-2xl font-semibold text-paper outline-none sm:text-3xl" initial={{ opacity: 0, y: reduce ? 0 : 10 }} animate={{ opacity: 1, y: 0 }} transition={t(0.8)}>
        {title}
      </motion.h3>
      <motion.div className="mt-3 max-w-md text-slate-light" initial={{ opacity: 0, y: reduce ? 0 : 10 }} animate={{ opacity: 1, y: 0 }} transition={t(0.95)}>
        {body}
      </motion.div>
      {reference && (
        <motion.div className="mt-7 flex items-center gap-2 rounded-2xl border border-amber/30 bg-amber/[0.06] py-2 pl-5 pr-2" initial={{ opacity: 0, y: reduce ? 0 : 10 }} animate={{ opacity: 1, y: 0 }} transition={t(1.1)}>
          <span className="text-xs uppercase tracking-[0.16em] text-slate">Reference</span>
          <span className="font-display text-lg font-semibold tracking-wider text-amber">{reference}</span>
          <button type="button" onClick={copy} className="ml-1 grid h-9 w-9 place-items-center rounded-full text-slate transition hover:bg-white/5 hover:text-paper" aria-label={copied ? 'Copied' : 'Copy reference number'}>
            {copied ? <Check className="h-4 w-4 text-amber" /> : <Copy className="h-4 w-4" />}
          </button>
        </motion.div>
      )}
      {children && (
        <motion.div className="mt-8 flex flex-wrap justify-center gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={t(1.25)}>
          {children}
        </motion.div>
      )}
    </motion.div>
  );
}
