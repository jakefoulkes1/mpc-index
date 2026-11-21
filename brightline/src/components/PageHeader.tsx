import { motion, useReducedMotion } from 'framer-motion';
import type { ReactNode } from 'react';
import { DrawnLine } from './BrightLine';

export function PageHeader({ eyebrow, title, intro, children }: { eyebrow: string; title: ReactNode; intro?: ReactNode; children?: ReactNode }) {
  const reduce = useReducedMotion();
  const fade = (d: number) => ({ initial: { opacity: 0, y: reduce ? 0 : 18 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.6, delay: reduce ? 0 : d, ease: [0.22, 1, 0.36, 1] as const } });
  return (
    <section className="relative overflow-hidden pb-16 pt-36 sm:pt-44 lg:pb-20">
      <div className="absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" aria-hidden="true" />
      <div className="absolute -top-40 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-amber/[0.07] blur-3xl" aria-hidden="true" />
      <div className="container-site relative">
        <motion.p className="eyebrow" {...fade(0)}>{eyebrow}</motion.p>
        <motion.h1 className="mt-6 max-w-4xl text-balance text-4xl font-bold leading-[1.05] text-paper sm:text-5xl lg:text-6xl" {...fade(0.08)}>
          {title}
        </motion.h1>
        {intro && <motion.p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-light sm:text-xl" {...fade(0.16)}>{intro}</motion.p>}
        {children && <motion.div className="mt-8" {...fade(0.24)}>{children}</motion.div>}
      </div>
      <DrawnLine className="absolute bottom-0 left-0 h-10" delay={0.3} duration={1.3} curve={false} />
    </section>
  );
}
