import type { Config } from "tailwindcss";

// Tailwind + shadcn-ready. Компоненты shadcn/ui добавляются JIT в P7 (Tier 0 UI).
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
