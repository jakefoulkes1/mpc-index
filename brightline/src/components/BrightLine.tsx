import { motion, useReducedMotion, useScroll, useSpring } from 'framer-motion';
import { useRef, type ReactNode } from 'react';
import { cn } from '../lib/utils';

/** Full-width line that draws itself across the screen. */
export function DrawnLine({ className, delay = 0.35, duration = 1.6, curve = true }: { className?: string; delay?: number; duration?: number; curve?: boolean }) {
  const reduce = useReducedMotion();
  const d = curve ? 'M0 60 C 360 60, 520 18, 760 30 S 1180 64, 1440 40' : 'M0 40 L1440 40';
  return (
    <svg className={cn('pointer-events-none w-full overflow-visible', className)} viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="bl-fade" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor="#F2B33D" stopOpacity="0" />
          <stop offset="0.12" stopColor="#F2B33D" />
          <stop offset="0.88" stopColor="#F2B33D" />
          <stop offset="1" stopColor="#F2B33D" stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* glow layer */}
      <motion.path
        d={d}
        fill="none"
        stroke="url(#bl-fade)"
        strokeWidth={6}
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        style={{ filter: 'blur(5px)' }}
        opacity={0.55}
        pathLength={1}
        strokeDasharray="1 1"
        initial={{ strokeDashoffset: reduce ? 0 : 1 }}
        animate={{ strokeDashoffset: 0 }}
        transition={{ duration: reduce ? 0 : duration, delay: reduce ? 0 : delay, ease: [0.65, 0, 0.35, 1] }}
      />
      <motion.path
        d={d}
        fill="none"
        stroke="url(#bl-fade)"
        strokeWidth={1.5}
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        pathLength={1}
        strokeDasharray="1 1"
        initial={{ strokeDashoffset: reduce ? 0 : 1 }}
        animate={{ strokeDashoffset: 0 }}
        transition={{ duration: reduce ? 0 : duration, delay: reduce ? 0 : delay, ease: [0.65, 0, 0.35, 1] }}
      />
    </svg>
  );
}

/** Amber underline that draws in when it scrolls into view. */
export function Underline({ children, className, delay = 0.2 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduce = useReducedMotion();
  return (
    <span className={cn('relative inline-block', className)}>
      {children}
      <motion.span
        aria-hidden="true"
        className="absolute -bottom-1.5 left-0 h-[2px] w-full origin-left rounded-full bg-amber shadow-glow"
        initial={{ scaleX: reduce ? 1 : 0 }}
        whileInView={{ scaleX: 1 }}
        viewport={{ once: true, amount: 0.8 }}
        transition={{ duration: reduce ? 0 : 0.9, delay: reduce ? 0 : delay, ease: [0.65, 0, 0.35, 1] }}
      />
    </span>
  );
}

/** Vertical line running down the page, filling in as the user scrolls through the wrapped content. */
export function ScrollSpine({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start 70%', 'end 70%'] });
  const scaleY = useSpring(scrollYProgress, { stiffness: 120, damping: 30, restDelta: 0.001 });
  return (
    <div ref={ref} className="relative">
      <div aria-hidden="true" className="pointer-events-none absolute bottom-0 left-[max(20px,calc((100vw-1200px)/2-8px))] top-0 hidden w-px bg-white/[0.06] lg:block">
        <motion.div style={{ scaleY }} className="absolute inset-0 origin-top bg-gradient-to-b from-amber via-amber to-amber/40 shadow-glow" />
      </div>
      {children}
    </div>
  );
}
