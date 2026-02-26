/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#fefdf8',
        'bg-secondary': '#f0fdf4',
        'bg-card': '#ffffff',
        'text-primary': '#1a2e1a',
        'text-secondary': '#6b7b6b',
        'accent-green': '#22c55e',
        'accent-dark': '#15803d',
        'accent-light': '#dcfce7',
        'accent-blue': '#3b82f6',
        'accent-orange': '#f59e0b',
        'accent-red': '#f87171',
        'accent-purple': '#a78bfa',
        'border': '#e5e7eb',
      },
    },
  },
  plugins: [],
}
