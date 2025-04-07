/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/*.{html,js}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FF6363',
        secondary: '#2E294E',
        'neutral-light': '#F5F5F5',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Poppins', 'sans-serif'],
      },
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: true,
    styled: true,
    base: true,
    utils: true,
    logs: true,
    rtl: false,
    prefix: "",
    darkTheme: "dark",
  },
}