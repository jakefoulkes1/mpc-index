import { cn, initials, monogramColours } from '../lib/utils';

export function Monogram({ name, size = 'md', className }: { name: string; size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const { bg, fg } = monogramColours(name);
  const dims = { sm: 'h-10 w-10 text-sm', md: 'h-14 w-14 text-base', lg: 'h-20 w-20 text-2xl' }[size];
  return (
    <span
      aria-hidden="true"
      className={cn('inline-grid shrink-0 place-items-center rounded-full font-display font-bold tracking-wide ring-1 ring-white/10', dims, className)}
      style={{ background: `radial-gradient(circle at 30% 25%, ${bg}, ${bg}cc 70%)`, color: fg }}
    >
      {initials(name)}
    </span>
  );
}

export function Avatar({ name, size = 'md', muted = false }: { name: string; size?: 'sm' | 'md' | 'lg'; muted?: boolean }) {
  const dims = { sm: 'h-12 w-12 text-base', md: 'h-16 w-16 text-xl', lg: 'h-24 w-24 text-3xl' }[size];
  return (
    <span aria-hidden="true" className={cn('relative inline-grid shrink-0 place-items-center rounded-full font-display font-semibold', dims, muted ? 'border border-dashed border-white/25 text-slate' : 'bg-gradient-to-br from-navy-600 to-navy-800 text-paper ring-1 ring-amber/60')}>
      {muted ? '+' : name.charAt(0)}
      {!muted && <span className="absolute bottom-0.5 right-0.5 h-3 w-3 rounded-full bg-amber shadow-glow ring-2 ring-navy" />}
    </span>
  );
}
