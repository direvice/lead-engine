import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
      },
      colors: {
        background: "#060606",
        accent: "#e8ff47",
        muted: "#737373",
        card: "#0c0c0c",
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(232, 255, 71, 0.15)",
        card: "0 1px 0 rgba(255,255,255,0.04) inset",
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out forwards",
        "pulse-soft": "pulseSoft 3s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
