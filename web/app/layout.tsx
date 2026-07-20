import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ai-code-reviewer",
  description: "Reviews a diff or PR for real bugs + security issues — not style.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
