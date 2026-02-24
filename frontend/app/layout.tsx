import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Chess vs Stockfish Pro",
  description: "Next-Gen Chess Interface with Robot Integration",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="overflow-hidden h-dvh">
      <body className={`${outfit.className} overflow-hidden h-dvh`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
