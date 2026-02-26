/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0f1419',
        'bg-secondary': '#1a2332',
        'bg-card': '#1e2d3d',
        'text-primary': '#e8eaed',
        'text-secondary': '#9aa0a6',
        'accent-green': '#34d399',
        'accent-blue': '#60a5fa',
        'accent-orange': '#fbbf24',
        'accent-red': '#f87171',
        'accent-purple': '#a78bfa',
      },
    },
  },
  plugins: [],
}
