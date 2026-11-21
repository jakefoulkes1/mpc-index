export type Status = 'Active' | 'Exited';

export interface Company {
  slug: string;
  name: string;
  oneLiner: string;
  sector: string;
  sectorGroup: string;
  region: string;
  stage: 'Series A' | 'Series B';
  year: number;
  status: Status;
  outcome?: string;
  featured?: boolean;
}

export const companies: Company[] = [
  { slug: 'andrux', name: 'Andrux', oneLiner: 'AI that helps life sciences teams run research faster and with fewer manual steps.', sector: 'AI life sciences', sectorGroup: 'Healthcare', region: 'Switzerland', stage: 'Series A', year: 2028, status: 'Active', featured: true },
  { slug: 'climatew', name: 'ClimateW', oneLiner: 'Climate technology that uses AI to automate environmental reporting.', sector: 'Climate tech and AI reporting', sectorGroup: 'Energy & climate', region: 'Africa', stage: 'Series A', year: 2027, status: 'Active', featured: true },
  { slug: 'pan-asian-qtc', name: 'Pan-Asian QTC', oneLiner: 'An AI studio building products for agriculture, aquaculture and health.', sector: 'AI studio', sectorGroup: 'Agriculture & health', region: 'Asia', stage: 'Series A', year: 2027, status: 'Active' },
  { slug: 'neynatech', name: 'NeyNaTech', oneLiner: 'A financial super-app that brings payments and everyday money tools into one place.', sector: 'Fintech super-app', sectorGroup: 'Finance', region: 'Tanzania', stage: 'Series B', year: 2027, status: 'Active', featured: true },
  { slug: 'irishstripe', name: 'IrishStripe', oneLiner: 'New materials and methods for the textile industry.', sector: 'Textile innovation', sectorGroup: 'Manufacturing', region: 'Ireland', stage: 'Series A', year: 2028, status: 'Active' },
  { slug: 'unocode', name: 'UnoCode', oneLiner: 'A platform that lets teams build business software without writing code.', sector: 'No-code platform', sectorGroup: 'Software', region: 'Ukraine', stage: 'Series A', year: 2027, status: 'Active' },
  { slug: 'noxtech', name: 'NoxTech', oneLiner: 'Business software sold to companies as a subscription service.', sector: 'B2B SaaS', sectorGroup: 'Software', region: 'UAE', stage: 'Series A', year: 2027, status: 'Exited', outcome: '10x return', featured: true },
  { slug: 'unbrk', name: 'UnBrk', oneLiner: 'Security software that helps organisations protect their systems and data.', sector: 'Security software', sectorGroup: 'Software', region: 'Undisclosed', stage: 'Series A', year: 2027, status: 'Exited' },
];

export const sectorGroups = Array.from(new Set(companies.map((c) => c.sectorGroup)));

export interface Person {
  slug: string;
  name: string;
  role: string;
  summary: string;
  bio: [string, string];
  linkedin: string;
}

// Bios are neutral, role-based text. Replace `bio` and `linkedin` with each person's real details.
export const team: Person[] = [
  { slug: 'vivien', name: 'Vivien', role: 'Managing Partner', summary: 'Leads the firm and its investment strategy.', bio: ['Vivien leads Brightline Ventures and sets the direction of the fund.', 'Works closely with founders on strategy, hiring and later funding rounds.'], linkedin: 'https://www.linkedin.com/' },
  { slug: 'sofia', name: 'Sofia', role: 'Fundraising Director', summary: 'Leads relationships with the fund’s investors.', bio: ['Sofia manages the fund’s relationships with its limited partners.', 'Leads fundraising and keeps investors informed about the fund.'], linkedin: 'https://www.linkedin.com/' },
  { slug: 'vera', name: 'Vera', role: 'Investment Director', summary: 'Leads new investments and supports portfolio companies.', bio: ['Vera leads new investments from first meeting to signed term sheet.', 'After we invest, works with founders on growth and selling to customers.'], linkedin: 'https://www.linkedin.com/' },
  { slug: 'sho', name: 'Sho', role: 'Dealflow Analyst', summary: 'Finds and reviews new companies for the fund.', bio: ['Sho finds new companies and runs the first review of every pitch.', 'Tracks the sectors and markets the fund invests in.'], linkedin: 'https://www.linkedin.com/' },
  { slug: 'jake', name: 'Jake', role: 'Fund Manager', summary: 'Runs fund operations, reporting and administration.', bio: ['Jake runs the day-to-day operations of the fund.', 'Leads reporting to investors and works with the fund’s service providers.'], linkedin: 'https://www.linkedin.com/' },
];

export const sectors = [
  { name: 'Energy', line: 'AI forecasts demand and spots faults early, so grids waste less power and crews fix problems before outages.' },
  { name: 'Manufacturing', line: 'AI checks quality on the line and plans maintenance, so factories lose fewer hours to defects and downtime.' },
  { name: 'Healthcare', line: 'AI handles paperwork, coding and scheduling, giving clinicians more time with patients.' },
  { name: 'Finance', line: 'AI reviews documents and flags risk in minutes, so teams spend less time on manual checks.' },
] as const;

export const steps = [
  { title: 'First meeting', line: 'A 45-minute call to understand the problem you solve, your customers and your team.' },
  { title: 'Deep dive', line: 'We spend time with your product, speak to customers and work through your numbers together.' },
  { title: 'Investment committee', line: 'You present to our investment committee, which makes every investment decision.' },
  { title: 'Term sheet', line: 'We send clear terms, explain each one, and agree them with you quickly.' },
  { title: 'Partnership', line: 'We get to work: hiring, sales introductions, new markets and support in later rounds.' },
] as const;

export const CONTACT_EMAIL = 'hello@brightlineventures.com';
export const OFFICE = { line1: '[Office address]', line2: 'Delaware, United States' };
