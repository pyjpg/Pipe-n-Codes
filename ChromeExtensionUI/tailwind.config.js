/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,html}",
    "./dist/**/*.{js,ts,jsx,tsx}"
  ],
  important: true, // This ensures Tailwind classes override page styles
  theme: {
    extend: {
      animation: {
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
      },
      keyframes: {
        'slide-in': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        }
      },
      zIndex: {
        'max': '2147483647',
      }
    },
  },
  plugins: [],
  // Prefix all classes to avoid conflicts with page styles
  // prefix: 'ext-',
  
  // Alternative: Use a CSS selector to scope Tailwind
  corePlugins: {
    preflight: false, // Disable Tailwind's base styles to avoid conflicts
  }
}