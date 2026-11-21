import { ArrowLeft } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { DrawnLine } from '../components/BrightLine';
import { usePageTitle } from '../components/Layout';

export default function NotFound() {
  usePageTitle('Page not found');
  const reduce = useReducedMotion();
  const { pathname } = useLocation();
  return (
    <section className="relative flex min-h-[85svh] flex-col justify-center overflow-hidden pb-16 pt-32">
      <div className="absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]" aria-hidden="true" />
      <div className="container-site relative text-center">
        <motion.p className="font-display text-[7rem] font-bold leading-none text-paper/10 sm:text-[11rem]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} aria-hidden="true">404</motion.p>
      </div>
      <DrawnLine className="relative -mt-14 h-16 sm:-mt-24 sm:h-20" curve={false} delay={0.2} />
      <div className="container-site relative text-center">
        <motion.div initial={{ opacity: 0, y: reduce ? 0 : 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduce ? 0 : 1.2 }}>
          <h1 className="mt-6 text-3xl font-semibold text-paper sm:text-4xl">This page is off the line.</h1>
          <p className="mx-auto mt-4 max-w-md text-slate-light">
            We could not find <span className="break-all font-medium text-paper">{pathname}</span>. It may have moved, or the link may be wrong.
          </p>
          <Link to="/" className="btn-primary mt-10">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back home
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
