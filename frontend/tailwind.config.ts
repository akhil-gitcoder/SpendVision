import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#ffffff",
          subtle: "#f8fafc",
        },
        brand: {
          50: "#eef4ff",
          100: "#dae6ff",
          200: "#b9d0ff",
          300: "#8bb0ff",
          400: "#5c8bff",
          500: "#3563e9",
          600: "#2748c9",
          700: "#1f39a3",
          800: "#1c3182",
          900: "#1b2c6b",
        },
        positive: "#16a34a",
        warning: "#d97706",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
