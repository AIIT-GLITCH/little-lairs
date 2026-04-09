import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Cascadia Code", "monospace"],
      },
      colors: {
        gh: {
          bg: "#0d1117",
          surface: "#161b22",
          border: "#30363d",
        },
      },
    },
  },
  plugins: [],
};

export default config;
