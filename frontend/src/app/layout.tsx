import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navigation from "@/components/Navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Learning Coach - Personalized Learning Digests",
  description: "Get personalized weekly AI learning digests tailored to your goals",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 min-h-screen`}>
        <Navigation />
        <main className="pt-20">
          {children}
        </main>
      </body>
    </html>
  );
}
