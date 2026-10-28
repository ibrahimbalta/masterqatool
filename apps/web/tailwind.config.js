/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#090614',
        surface: {
          50: '#231b40',
          100: '#1c1634',
          200: '#161129',
          300: '#110d20',
          400: '#0c0818',
        },
        border: '#272044',
        brand: {
          orange: '#ff6b00',
          orangeHover: '#ff8533',
          orangeMuted: 'rgba(255, 107, 0, 0.15)',
        },
        status: {
          passed: '#10b981',
          failed: '#ef4444',
          blocked: '#eab308',
          queued: '#8b5cf6',
          running: '#3b82f6',
          cancelled: '#6b7280',
          flaky: '#ec4899',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
