import { AlertCircle } from 'lucide-react';
import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '../lib/utils';

interface Base {
  label: string;
  error?: string;
  hint?: ReactNode;
  optional?: boolean;
  className?: string;
}

function Wrapper({ id, label, error, hint, optional, className, children }: Base & { id: string; children: ReactNode }) {
  return (
    <div className={className}>
      <label htmlFor={id} className="field-label">
        {label}
        {optional ? <span className="ml-1.5 font-normal text-slate">(optional)</span> : <span className="ml-0.5 text-amber" aria-hidden="true">*</span>}
      </label>
      {children}
      {hint && !error && <p id={`${id}-hint`} className="mt-1.5 text-sm text-slate">{hint}</p>}
      <AnimatePresence initial={false}>
        {error && (
          <motion.p
            id={`${id}-error`}
            className="field-error"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.18 }}
          >
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}

function describedBy(id: string, error?: string, hint?: ReactNode) {
  return error ? `${id}-error` : hint ? `${id}-hint` : undefined;
}

type InputProps = Base & Omit<InputHTMLAttributes<HTMLInputElement>, 'className'>;
export function TextField({ label, error, hint, optional, className, ...rest }: InputProps) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} error={error} hint={hint} optional={optional} className={className}>
      <input id={id} className="field-input" aria-invalid={error ? true : undefined} aria-required={!optional} aria-describedby={describedBy(id, error, hint)} {...rest} />
    </Wrapper>
  );
}

type SelectProps = Base & Omit<SelectHTMLAttributes<HTMLSelectElement>, 'className'> & { options: readonly string[]; placeholder: string };
export function SelectField({ label, error, hint, optional, className, options, placeholder, ...rest }: SelectProps) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} error={error} hint={hint} optional={optional} className={className}>
      <select id={id} className={cn('field-input', !rest.value && 'text-slate')} aria-invalid={error ? true : undefined} aria-required={!optional} aria-describedby={describedBy(id, error, hint)} {...rest}>
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </Wrapper>
  );
}

type AreaProps = Base & Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'>;
export function TextArea({ label, error, hint, optional, className, ...rest }: AreaProps) {
  const id = useId();
  return (
    <Wrapper id={id} label={label} error={error} hint={hint} optional={optional} className={className}>
      <textarea id={id} rows={5} className="field-input resize-y" aria-invalid={error ? true : undefined} aria-required={!optional} aria-describedby={describedBy(id, error, hint)} {...rest} />
    </Wrapper>
  );
}
