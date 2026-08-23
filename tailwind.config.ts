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
          ink: "#202123",
          muted: "#62666d",
          line: "#dfe3e8",
          panel: "#f7f8fa",
          surface: "#ffffff",
          accent: "#23685a",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
