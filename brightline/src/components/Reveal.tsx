import { motion, useReducedMotion, type HTMLMotionProps } from 'framer-motion';

type Props = HTMLMotionProps<'div'> & { delay?: number; y?: number };

export function Reveal({ delay = 0, y = 28, children, ...rest }: Props) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? { opacity: 0 } : { opacity: 0, y }}
      whileInView={reduce ? { opacity: 1 } : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: reduce ? 0.2 : 0.7, delay: reduce ? 0 : delay, ease: [0.22, 1, 0.36, 1] }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export function SectionHeading({ eyebrow, title, intro, className, id }: { eyebrow: string; title: React.ReactNode; intro?: React.ReactNode; className?: string; id?: string }) {
  return (
    <Reveal className={className}>
      <p className="eyebrow">{eyebrow}</p>
      <h2 id={id} className="mt-5 max-w-3xl text-balance text-3xl font-semibold leading-[1.1] text-paper sm:text-4xl lg:text-5xl">{title}</h2>
      {intro && <p className="mt-5 max-w-2xl text-lg leading-relaxed text-slate-light">{intro}</p>}
    </Reveal>
  );
}
