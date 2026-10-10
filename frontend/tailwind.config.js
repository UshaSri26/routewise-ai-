/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#07111F',
          900: '#0C1829',
          850: '#10223A',
          800: '#162B48',
          700: '#1E3A5F',
        },
        teal: {
          DEFAULT: '#21D4C2',
          hover: '#1ABC9C',
          muted: 'rgba(33, 212, 194, 0.15)',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
