/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"STIX Two Text"', 'Georgia', '"Times New Roman"', 'serif'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        handwriting: ['Caveat', '"Segoe Script"', 'cursive', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      colors: {
        ivory: {
          50: '#FFFFFF',
          100: '#FBF7EE', // Classic warm ivory paper
          200: '#F5EFE0',
          300: '#EDE3CE',
          400: '#DFD3B9',
          500: '#CEC0A2',
        },
        navy: {
          DEFAULT: '#102A43', // Deep textbook navy ink
          dark: '#0A1C2E',
          secondary: '#334E68',
          muted: '#627D98',
          faint: '#9FB3C8',
        },
        vermilion: {
          DEFAULT: '#D9381E', // Vibrant vermilion red annotation ink
          dark: '#B82C15',
          light: '#FDF2F0',
          border: '#F8C8C2',
          note: '#C83214',
        },
        sage: {
          50: '#F0F8F3',
          100: '#DCF0E2',
          700: '#1A5336',
          800: '#134029',
        }
      },
      boxShadow: {
        textbook: '0 2px 4px rgba(16, 42, 67, 0.04), 0 1px 2px rgba(16, 42, 67, 0.02)',
        'textbook-hover': '0 6px 16px rgba(16, 42, 67, 0.07), 0 2px 4px rgba(16, 42, 67, 0.03)',
      }
    },
  },
  plugins: [],
};
