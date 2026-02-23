/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        claude: {
          // Dark theme — warm stone (matches Claude Code)
          bg: '#1c1917',
          'bg-secondary': '#292524',
          'bg-tertiary': '#3c3836',
          surface: '#292524',
          'surface-hover': '#3c3836',
          // Coral-orange accent (Claude brand)
          orange: '#da7756',
          'orange-hover': '#c96b4d',
          'orange-light': '#e08e78',
          // Text — warm off-white / stone grays
          text: '#ede9e3',
          'text-secondary': '#a8a29e',
          'text-muted': '#78716c',
          // Borders — warm stone
          border: '#44403c',
          'border-light': '#57534e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
