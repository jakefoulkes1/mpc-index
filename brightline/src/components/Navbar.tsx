import { AnimatePresence, motion, useMotionValueEvent, useReducedMotion, useScroll } from 'framer-motion';
import { ArrowUpRight, Menu, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import { Logo } from './Logo';

export const NAV = [
  { to: '/portfolio', label: 'Portfolio' },
  { to: '/team', label: 'Team' },
  { to: '/founders', label: 'Founders' },
  { to: '/investors', label: 'Investors' },
  { to: '/contact', label: 'Contact' },
];

export function Navbar() {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const reduce = useReducedMotion();
  const panelRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  useMotionValueEvent(scrollY, 'change', (y) => setScrolled(y > 24));
  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const first = panelRef.current?.querySelector<HTMLElement>('a, button');
    first?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        toggleRef.current?.focus();
      }
      if (e.key === 'Tab' && panelRef.current) {
        const items = Array.from(panelRef.current.querySelectorAll<HTMLElement>('a, button'));
        const f = items[0], l = items[items.length - 1];
        if (e.shiftKey && document.activeElement === f) { e.preventDefault(); l.focus(); }
        else if (!e.shiftKey && document.activeElement === l) { e.preventDefault(); f.focus(); }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = prev;
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <>
      <header className={cn('fixed inset-x-0 top-0 z-[60] transition-all duration-300', scrolled ? 'glass' : 'border-b border-transparent bg-transparent')}>
        <div className={cn('container-site flex items-center justify-between transition-[height] duration-300', scrolled ? 'h-16' : 'h-20 lg:h-24')}>
          <Logo />
          <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => cn('relative rounded-full px-4 py-2 text-[15px] font-medium transition-colors', isActive ? 'text-paper' : 'text-slate-light hover:text-paper')}>
                {({ isActive }) => (
                  <>
                    {item.label}
                    {isActive && (
                      <motion.span layoutId="nav-active" className="absolute inset-x-4 -bottom-0.5 h-[2px] rounded-full bg-amber shadow-glow" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />
                    )}
                  </>
                )}
              </NavLink>
            ))}
            <Link to="/founders" className="btn-primary ml-3 min-h-[42px] px-5 py-2 text-sm">
              Pitch us <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </nav>
          <button
            ref={toggleRef}
            type="button"
            className="grid h-11 w-11 place-items-center rounded-full border border-white/15 text-paper transition hover:border-amber/60 lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      <AnimatePresence>
        {open && (
          <>
            <motion.div className="fixed inset-0 z-[55] bg-[#050B15]/70 backdrop-blur-sm lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)} aria-hidden="true" />
            <motion.div
              ref={panelRef}
              id="mobile-menu"
              role="dialog"
              aria-modal="true"
              aria-label="Menu"
              className="fixed bottom-0 right-0 top-0 z-[65] flex w-[min(86vw,380px)] flex-col border-l border-white/10 bg-navy-800 px-6 pb-8 pt-6 lg:hidden"
              initial={reduce ? { opacity: 0 } : { x: '100%' }}
              animate={reduce ? { opacity: 1 } : { x: 0 }}
              exit={reduce ? { opacity: 0 } : { x: '100%' }}
              transition={{ type: 'spring', stiffness: 380, damping: 38 }}
            >
              <div className="absolute bottom-0 left-0 top-0 w-px bg-gradient-to-b from-transparent via-amber to-transparent shadow-glow" aria-hidden="true" />
              <div className="flex items-center justify-between">
                <Logo onClick={() => setOpen(false)} />
                <button type="button" onClick={() => { setOpen(false); toggleRef.current?.focus(); }} className="grid h-11 w-11 place-items-center rounded-full border border-white/15 text-paper" aria-label="Close menu">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <nav aria-label="Mobile" className="mt-10 flex flex-col">
                {[{ to: '/', label: 'Home' }, ...NAV].map((item, i) => (
                  <motion.div key={item.to} initial={reduce ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: reduce ? 0 : 0.08 + i * 0.04 }}>
                    <NavLink
                      to={item.to}
                      end
                      onClick={() => setOpen(false)}
                      className={({ isActive }) => cn('flex items-center justify-between border-b border-white/[0.07] py-4 font-display text-2xl font-medium transition-colors', isActive ? 'text-amber' : 'text-paper hover:text-amber')}
                    >
                      {item.label}
                    </NavLink>
                  </motion.div>
                ))}
              </nav>
              <Link to="/founders" onClick={() => setOpen(false)} className="btn-primary mt-auto w-full">
                Pitch us <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
