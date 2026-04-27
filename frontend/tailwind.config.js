export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#FF8400",
        sidebar: { DEFAULT: "#E7E8E5", border: "#CBCCC9", foreground: "#666666", accent: "#CBCCC9" },
        muted: { DEFAULT: "#F2F3F0", foreground: "#666666" },
        border: "#CBCCC9",
        card: "#FFFFFF",
        background: "#F2F3F0",
        foreground: "#111111",
      },
      fontFamily: {
        primary: ['"JetBrains Mono"', 'monospace'],
        secondary: ['"Geist"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
