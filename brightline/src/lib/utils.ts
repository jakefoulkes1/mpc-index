export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(' ');
}

export function initials(name: string) {
  const words = name.replace(/[^A-Za-z0-9 -]/g, '').split(/[\s-]+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  // Split CamelCase names: "NeyNaTech" -> "NT"
  const caps = name.match(/[A-Z]/g) ?? [];
  if (caps.length >= 2) return (caps[0] + caps[caps.length - 1]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

const MONOGRAM_COLOURS = [
  ['#F2B33D', '#0F1B2D'],
  ['#5EC2B7', '#0F1B2D'],
  ['#8FA8FF', '#0F1B2D'],
  ['#E88A6E', '#0F1B2D'],
  ['#B79CF2', '#0F1B2D'],
  ['#7FD18B', '#0F1B2D'],
  ['#F2D06B', '#0F1B2D'],
  ['#6FB3E8', '#0F1B2D'],
] as const;

export function monogramColours(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  const [bg, fg] = MONOGRAM_COLOURS[h % MONOGRAM_COLOURS.length];
  return { bg, fg };
}
