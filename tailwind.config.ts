import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Geist", "Satoshi", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        shell: {
          // Dark readable palette — neutral surfaces, single teal accent.
          ink: "#e8eaed",
          muted: "#9aa0a8",
          line: "#2b2f36",
          panel: "#16181c",
          surface: "#1e2126",
          accent: "#58b6a0",
          "accent-hover": "#79cab6",
          "accent-solid": "#215f51",
          "accent-solid-hover": "#1a4c41",
          "accent-subtle": "#17302a",
          "accent-subtle-hover": "#1e3d35",
          destructive: "#ef8078",
          "destructive-hover": "#f59c95",
          "destructive-solid": "#a12b24",
          "destructive-solid-hover": "#86221c",
          "destructive-subtle": "#2c1917",
          warning: "#dfae55",
          "warning-hover": "#ecc46f",
          "warning-subtle": "#2c2211",
          focus: "#58b6a0",
        },
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-up": "slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-subtle": "pulseSubtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
