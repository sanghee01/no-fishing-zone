import { globalCss } from "@devup-ui/react";

globalCss({
  "*": {
    boxSizing: "border-box",
    m: 0,
    p: 0,
  },
  "html, body": {
    maxW: "100vw",
    overflowX: "hidden",
  },
  body: {
    bg: "var(--background)",
    color: "var(--foreground)",
    fontFamily:
      '"Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    lineHeight: 1.6,
  },
  "h1, h2, h3, h4, h5, h6": {
    fontWeight: 600,
    lineHeight: 1.2,
    mb: "1rem",
  },
  h1: { fontSize: "2rem" },
  h2: { fontSize: "1.5rem" },
  p: { mb: "1rem" },
  a: {
    color: "inherit",
    textDecoration: "none",
    cursor: "pointer",
  },
});
