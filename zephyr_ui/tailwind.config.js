/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        zephyr: {
          primary: "var(--zephyr-primary)",
          secondary: "var(--zephyr-secondary)",
          accent: "var(--zephyr-accent)",
          bg: "var(--zephyr-bg)",
          surface: "var(--zephyr-surface)",
          text: "var(--zephyr-text)",
          muted: "var(--zephyr-muted)",
          border: "var(--zephyr-border)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "float": "float 3s ease-in-out infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "slide-up": "slideUp 0.3s ease-out",
        "fade-in": "fadeIn 0.2s ease-out",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        glow: {
          from: { boxShadow: "0 0 5px var(--zephyr-accent)" },
          to: { boxShadow: "0 0 20px var(--zephyr-accent)" },
        },
        slideUp: {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
