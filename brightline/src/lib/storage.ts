export type FormKind = 'pitches' | 'lp-requests' | 'messages';

export interface Stored<T> {
  reference: string;
  submittedAt: string;
  data: T;
}

const key = (kind: FormKind) => `brightline:${kind}`;

export function makeReference(prefix: string) {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const bytes = new Uint8Array(6);
  crypto.getRandomValues(bytes);
  const body = Array.from(bytes, (b) => alphabet[b % alphabet.length]).join('');
  return `${prefix}-${body.slice(0, 3)}-${body.slice(3)}`;
}

export function saveSubmission<T>(kind: FormKind, data: T, prefix: string): Stored<T> {
  const entry: Stored<T> = { reference: makeReference(prefix), submittedAt: new Date().toISOString(), data };
  try {
    const existing = JSON.parse(localStorage.getItem(key(kind)) ?? '[]') as Stored<T>[];
    localStorage.setItem(key(kind), JSON.stringify([...existing, entry]));
  } catch {
    // Storage can be unavailable (private mode, quota). The success state still shows the reference.
  }
  return entry;
}

export function readSubmissions<T>(kind: FormKind): Stored<T>[] {
  try {
    return JSON.parse(localStorage.getItem(key(kind)) ?? '[]') as Stored<T>[];
  } catch {
    return [];
  }
}
