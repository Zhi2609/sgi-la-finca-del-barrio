/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html", "./app/**/*.py"],
  theme: {
    extend: {
      colors: {
        vino: {
          50: "#fdf3f4",
          100: "#fbe6e8",
          200: "#f6d0d5",
          500: "#8e2438",
          700: "#631928",
          800: "#4e1623",
          900: "#350e17",
          950: "#1f070c"
        },
        oro: {
          100: "#f9f1dc",
          300: "#e5ca87",
          500: "#c59b42",
          600: "#a87f2b",
          700: "#84611e"
        },
        crema: {
          50: "#faf6f0",
          100: "#f3ece0",
          200: "#e5d9c5"
        }
      }
    }
  },
  plugins: []
};
