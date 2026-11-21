/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#0F1B2D', 900: '#0A1322', 800: '#132238', 700: '#1A2C46', 600: '#243A5A' },
        paper: '#F6F4EE',
        amber: { DEFAULT: '#F2B33D', soft: '#F6C463', deep: '#C98A12' },
        slate: { DEFAULT: '#8A94A6', light: '#AEB6C4' },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', '-apple-system', '"Segoe UI"', 'sans-serif'],
      },
      maxWidth: { site: '1200px' },
      boxShadow: {
        glow: '0 0 12px rgba(242,179,61,.55), 0 0 2px rgba(242,179,61,.9)',
        card: '0 24px 60px -30px rgba(0,0,0,.65)',
      },
    },
  },
  plugins: [],
};
