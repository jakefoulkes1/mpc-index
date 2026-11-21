import { useCallback, useState } from 'react';
import { runRules, type Schema } from './validation';

export function useForm<K extends string>(initial: Record<K, string>, schema: Schema<K>) {
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState<Partial<Record<K, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<K, boolean>>>({});

  const setField = useCallback(
    (name: K, value: string) => {
      setValues((v) => ({ ...v, [name]: value }));
      // Re-validate live once a field has been touched, so errors clear as the user fixes them.
      setErrors((e) => (touched[name] || e[name] ? { ...e, [name]: runRules(value, schema[name]) ?? undefined } : e));
    },
    [schema, touched],
  );

  const blur = useCallback(
    (name: K) => {
      setTouched((t) => ({ ...t, [name]: true }));
      setErrors((e) => ({ ...e, [name]: runRules(values[name], schema[name]) ?? undefined }));
    },
    [schema, values],
  );

  /** Validate a subset (or all) fields. Returns the first invalid field name, or null. */
  const check = useCallback(
    (names: K[] = Object.keys(schema) as K[]) => {
      const next: Partial<Record<K, string>> = {};
      let first: K | null = null;
      names.forEach((n) => {
        const err = runRules(values[n], schema[n]);
        if (err) {
          next[n] = err;
          if (!first) first = n;
        }
      });
      setErrors((e) => {
        const merged = { ...e };
        names.forEach((n) => (merged[n] = next[n]));
        return merged;
      });
      setTouched((t) => ({ ...t, ...Object.fromEntries(names.map((n) => [n, true])) }));
      return first as K | null;
    },
    [schema, values],
  );

  const reset = useCallback(() => {
    setValues(initial);
    setErrors({});
    setTouched({});
  }, [initial]);

  const bind = (name: K) => ({
    name,
    value: values[name],
    error: errors[name],
    onChange: (e: { target: { value: string } }) => setField(name, e.target.value),
    onBlur: () => blur(name),
  });

  return { values, errors, bind, check, reset, setField };
}

export function focusField(formId: string, name: string) {
  const el = document.querySelector<HTMLElement>(`#${formId} [name="${name}"]`);
  el?.focus();
}
