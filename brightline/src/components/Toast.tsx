import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { CheckCircle2, X } from 'lucide-react';
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

interface Toast { id: number; title: string; body?: string }
const Ctx = createContext<(t: Omit<Toast, 'id'>) => void>(() => {});
export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);
  const reduce = useReducedMotion();

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const push = useCallback(
    (t: Omit<Toast, 'id'>) => {
      const id = nextId.current++;
      setToasts((list) => [...list, { ...t, id }]);
      window.setTimeout(() => dismiss(id), 6000);
    },
    [dismiss],
  );

  return (
    <Ctx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-[90] flex flex-col items-center gap-3 p-4 sm:items-end sm:p-6" role="status" aria-live="polite">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout={!reduce}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 24, scale: 0.96 }}
              animate={reduce ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
              exit={reduce ? { opacity: 0 } : { opacity: 0, x: 40 }}
              transition={{ type: 'spring', stiffness: 400, damping: 32 }}
              className="pointer-events-auto relative flex w-full max-w-sm items-start gap-3 overflow-hidden rounded-2xl border border-amber/30 bg-navy-800/95 p-4 pr-12 shadow-card backdrop-blur-xl"
            >
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-amber" aria-hidden="true" />
              <div>
                <p className="font-semibold text-paper">{t.title}</p>
                {t.body && <p className="mt-0.5 text-sm text-slate-light">{t.body}</p>}
              </div>
              <button type="button" onClick={() => dismiss(t.id)} className="absolute right-2 top-2 grid h-9 w-9 place-items-center rounded-full text-slate hover:bg-white/5 hover:text-paper" aria-label="Dismiss notification">
                <X className="h-4 w-4" />
              </button>
              <motion.span
                aria-hidden="true"
                className="absolute bottom-0 left-0 h-[2px] w-full origin-left bg-amber"
                initial={{ scaleX: 1 }}
                animate={{ scaleX: 0 }}
                transition={{ duration: 6, ease: 'linear' }}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </Ctx.Provider>
  );
}
