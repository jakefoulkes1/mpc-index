export type Rule = (value: string) => string | null;

export const required = (msg = 'This field is required.'): Rule => (v) => (v.trim() ? null : msg);
export const minLength = (n: number, msg?: string): Rule => (v) =>
  v.trim().length >= n ? null : msg ?? `Please use at least ${n} characters.`;
export const maxLength = (n: number): Rule => (v) => (v.trim().length <= n ? null : `Please keep this under ${n} characters.`);
export const email: Rule = (v) => (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) ? null : 'Enter a valid email, like name@company.com.');
export const website: Rule = (v) =>
  /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(:\d+)?(\/\S*)?$/i.test(v.trim()) ? null : 'Enter a valid website, like company.com.';

export function runRules(value: string, rules: Rule[]) {
  for (const rule of rules) {
    const err = rule(value);
    if (err) return err;
  }
  return null;
}

export type Schema<K extends string> = Record<K, Rule[]>;

export function validate<K extends string>(values: Record<K, string>, schema: Schema<K>) {
  const errors: Partial<Record<K, string>> = {};
  (Object.keys(schema) as K[]).forEach((k) => {
    const e = runRules(values[k] ?? '', schema[k]);
    if (e) errors[k] = e;
  });
  return errors;
}
