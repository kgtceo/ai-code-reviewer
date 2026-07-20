import type { Metadata } from "next";
import "./globals.css";

const url = "https://reviewer.kareemghazal.com";
const title = "ai-code-reviewer — real bugs in a diff/PR, not style";
const description =
  "Reviews a diff or GitHub PR for real bugs and security issues — not style — pinning each finding to a changed line and scoring itself on a planted-bug test set. Live + open-source.";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url,
    siteName: "ai-code-reviewer",
    title,
    description,
    locale: "en_GB",
    images: [
      {
        url: "/og.jpg",
        width: 1200,
        height: 630,
        alt: "ai-code-reviewer — bug and security review for diffs and PRs",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/og.jpg"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
