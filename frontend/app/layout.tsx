import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import { ThemeScript } from "@devup-ui/react";

export const metadata: Metadata = {
  title: "낚시금지구역",
  icons: {
    icon: "/images/logo.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body>{children}</body>
    </html>
  );
}
