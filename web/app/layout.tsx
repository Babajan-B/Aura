import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura Watch — Wearable Seizure-Safety Research Prototype",
  description:
    "Aura Watch is a watch-and-phone research prototype for wearable monitoring, user confirmation and caregiver-alert workflows.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-display text-slate-200 antialiased selection:bg-neon-cyan/30">
        <div className="grid-bg" aria-hidden />
        {children}
      </body>
    </html>
  );
}
