import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { useLocation, useOutlet } from 'react-router-dom';
import { Footer } from './Footer';
import { Navbar } from './Navbar';
import { ScrollProgress } from './ScrollProgress';

export function Layout() {
  const location = useLocation();
  const outlet = useOutlet();
  const reduce = useReducedMotion();
  const mainRef = useRef<HTMLElement>(null);
  const firstRender = useRef(true);

  const onExitComplete = () => {
    const hash = location.hash.slice(1);
    const target = hash ? document.getElementById(hash) : null;
    if (target) target.scrollIntoView();
    else window.scrollTo(0, 0);
    // Move focus to the new page so keyboard and screen reader users start at the top.
    mainRef.current?.focus({ preventScroll: true });
  };

  // Handle a hash on first load (e.g. /#portfolio).
  useEffect(() => {
    if (!firstRender.current) return;
    firstRender.current = false;
    if (location.hash) {
      window.setTimeout(() => document.getElementById(location.hash.slice(1))?.scrollIntoView(), 120);
    }
  }, [location.hash]);

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only z-[100] rounded-full bg-amber px-5 py-3 font-semibold text-navy focus:not-sr-only focus:fixed focus:left-4 focus:top-4">
        Skip to content
      </a>
      <ScrollProgress />
      <Navbar />
      <main id="main" ref={mainRef} tabIndex={-1} className="flex-1 outline-none">
        <AnimatePresence mode="wait" initial={false} onExitComplete={onExitComplete}>
          <motion.div
            key={location.pathname}
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: 16 }}
            animate={reduce ? { opacity: 1 } : { opacity: 1, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, y: -12 }}
            transition={{ duration: reduce ? 0.15 : 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            {outlet}
          </motion.div>
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  );
}

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} — Brightline Ventures` : 'Brightline Ventures — Backing AI that runs the real economy';
  }, [title]);
}
