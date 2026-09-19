import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura Watch — On-Device Seizure Pre-Ictal Guardian",
  description:
    "Sub-500ms on-device seizure pre-ictal detection running RGF-Net (37,554 params) on Wear OS.",
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
