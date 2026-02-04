import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "낚시금지구역",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
