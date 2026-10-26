/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0c',
          800: '#121214',
          700: '#1c1c1f',
          600: '#2a2a2e'
        },
        primary: {
          500: '#3b82f6',
          400: '#60a5fa'
        },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b'
      }
    },
  },
  plugins: [],
}
