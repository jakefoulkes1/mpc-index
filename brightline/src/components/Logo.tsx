import { Link } from 'react-router-dom';
import { cn } from '../lib/utils';

export function Logo({ className, onClick }: { className?: string; onClick?: () => void }) {
  return (
    <Link to="/" onClick={onClick} className={cn('group inline-flex items-center gap-3 rounded-lg font-display text-[17px] font-semibold tracking-tight text-paper', className)} aria-label="Brightline Ventures home">
      <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0" aria-hidden="true">
        <rect x="1" y="1" width="30" height="30" rx="9" fill="none" stroke="currentColor" strokeOpacity=".3" strokeWidth="1.5" />
        <path d="M6.5 21 L25.5 11" stroke="#F2B33D" strokeWidth="2.5" strokeLinecap="round" className="drop-shadow-[0_0_4px_rgba(242,179,61,.8)] transition-transform duration-300 group-hover:translate-x-0.5" />
      </svg>
      <span>Brightline<span className="text-slate"> Ventures</span></span>
    </Link>
  );
}
