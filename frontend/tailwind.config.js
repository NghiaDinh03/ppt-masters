/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#5b8def',
        'primary-light': '#88aaff',
        dark: '#161618',
        darker: '#0d0d0f',
        surface: '#16161a',
        'surface-hover': '#1d1d20',
        border: '#26262a',
      },
    },
  },
  plugins: [],
};
