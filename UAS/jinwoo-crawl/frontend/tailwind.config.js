/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        brand: {
          bg: '#090d16',
          card: '#0f172a',
          hover: '#162038',
          border: '#1e293b',
        },
        category: {
          disaster: '#ea580c',
          politics: '#3b82f6',
          economy: '#10b981',
          tech: '#8b5cf6',
          social: '#06b6d4',
          breaking: '#ef4444',
        }
      }
    },
  },
  plugins: [],
};
