import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "InsightFlow AI — Autonomous Business Intelligence Platform",
  description:
    "Autonomous Business Intelligence Agent platform providing automated statistical exploratory data analysis, root-cause variance attribution, and probabilistic forecasting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable}`}>
      <body className={`${inter.className} antialiased bg-[var(--background)] text-slate-200 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
