import { cn } from '../lib/utils';

export function StatusPill({ status, outcome }: { status: 'Active' | 'Exited'; outcome?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider', status === 'Active' ? 'bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/25' : 'bg-amber/10 text-amber ring-1 ring-amber/30')}>
      <span className={cn('h-1.5 w-1.5 rounded-full', status === 'Active' ? 'bg-emerald-300' : 'bg-amber')} aria-hidden="true" />
      {status}
      {outcome && <span className="normal-case tracking-normal opacity-80">· {outcome.replace(' return', '')}</span>}
    </span>
  );
}
