import type { Config } from "tailwindcss";

// Tailwind CSS 4 loads this file through the @config directive in src/app/globals.css.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
