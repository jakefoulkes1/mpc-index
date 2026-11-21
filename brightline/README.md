# Brightline Ventures website

React + TypeScript + Tailwind CSS + Framer Motion + React Router + lucide-react, built with Vite.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-checks, then outputs static files to dist/
npm run preview    # serves dist/ at http://localhost:4173
```

## Pages

`/` home story · `/portfolio` · `/team` · `/founders` · `/investors` · `/contact` · anything else shows the 404 page.

Portfolio filters and the open company are stored in the URL (e.g. `/portfolio?status=exited&company=noxtech`), so every view can be linked to.

## Forms

There is no backend. Each form validates inline, then saves to `localStorage` and shows a success state with a reference number:

| Form | localStorage key |
| --- | --- |
| Pitch (/founders) | `brightline:pitches` |
| LP information (/investors) | `brightline:lp-requests` |
| Contact (/contact) | `brightline:messages` |

Submissions stay in the visitor's own browser. Connect a real endpoint in `src/lib/storage.ts` before launch.

## Content to replace

All content lives in `src/data.ts`: companies, team bios and LinkedIn URLs, and the office address (`[Office address]`).

## Deploying under a sub-path

The app uses browser routing. For a host such as GitHub Pages under `/repo-name/`, build with `BASE_PATH=/repo-name/ npm run build` and configure the host to serve `index.html` for unknown paths (on GitHub Pages, copy `dist/index.html` to `dist/404.html`).
