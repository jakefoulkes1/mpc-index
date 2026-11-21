import { Mail } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CONTACT_EMAIL } from '../data';
import { Logo } from './Logo';
import { NAV } from './Navbar';

export function Footer() {
  return (
    <footer className="relative border-t border-white/[0.06] bg-navy-900">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber/70 to-transparent" aria-hidden="true" />
      <div className="container-site grid gap-12 py-16 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-5 max-w-xs text-slate-light">Backing AI that runs the real economy.</p>
          <a href={`mailto:${CONTACT_EMAIL}`} className="mt-6 inline-flex items-center gap-2 rounded text-paper transition hover:text-amber">
            <Mail className="h-4 w-4" aria-hidden="true" /> {CONTACT_EMAIL}
          </a>
        </div>
        <nav aria-label="Footer">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate">Explore</p>
          <ul className="mt-4 space-y-3">
            <li><Link to="/" className="text-slate-light transition hover:text-paper">Home</Link></li>
            {NAV.map((n) => (
              <li key={n.to}><Link to={n.to} className="text-slate-light transition hover:text-paper">{n.label}</Link></li>
            ))}
          </ul>
        </nav>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate">Entities</p>
          <ul className="mt-4 space-y-3 text-slate-light">
            <li>Brightline Ventures Fund I, L.P.</li>
            <li>Brightline Ventures Management, LLC</li>
            <li>Delaware, US</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/[0.06]">
        <div className="container-site flex flex-col gap-3 py-6 text-sm text-slate md:flex-row md:items-center md:justify-between">
          <p>© 2026 Brightline Ventures Management, LLC. All rights reserved.</p>
          <p className="max-w-xl md:text-right">Nothing on this website is an offer to sell, or a request for an offer to buy, any security.</p>
        </div>
      </div>
    </footer>
  );
}
