import { AlertCircle, Check } from 'lucide-react';
import { useId, type ReactNode } from 'react';
import { cn } from '../lib/utils';

export function Checkbox({ name, checked, onChange, error, children }: { name: string; checked: boolean; onChange: (v: boolean) => void; error?: string; children: ReactNode }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="group flex cursor-pointer items-start gap-3">
        <span className="relative mt-0.5 shrink-0">
          <input
            id={id}
            name={name}
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? `${id}-error` : undefined}
            className="peer absolute inset-0 h-6 w-6 cursor-pointer opacity-0"
          />
          <span
            aria-hidden="true"
            className={cn(
              'grid h-6 w-6 place-items-center rounded-md border transition peer-focus-visible:ring-2 peer-focus-visible:ring-amber peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-navy-800',
              checked ? 'border-amber bg-amber text-navy' : error ? 'border-red-400/80' : 'border-white/25 group-hover:border-white/50',
            )}
          >
            {checked && <Check className="h-4 w-4" strokeWidth={3} />}
          </span>
        </span>
        <span className="text-[15px] leading-relaxed text-slate-light">{children}</span>
      </label>
      {error && (
        <p id={`${id}-error`} className="field-error ml-9">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> {error}
        </p>
      )}
    </div>
  );
}
