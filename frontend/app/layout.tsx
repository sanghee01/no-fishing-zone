import type { Metadata } from "next";
import React from "react";
import { ThemeScript } from "@devup-ui/react";
import "@/app/globalCss";

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
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
