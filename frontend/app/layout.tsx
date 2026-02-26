import type { Metadata } from "next";
import { Playfair_Display, Roboto } from "next/font/google";
import "./globals.css";

const playfair = Playfair_Display({ 
  subsets: ["latin"],
  variable: "--font-playfair",
  weight: ["400", "600", "700", "900"]
});

const roboto = Roboto({ 
  subsets: ["latin"],
  variable: "--font-roboto",
  weight: ["300", "400", "500", "700"]
});

export const metadata: Metadata = {
  title: "ChessRobot",
  description: "Next-Gen Chess Interface with Robot Integration",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="overflow-hidden h-dvh">
      <body className={`${playfair.variable} ${roboto.variable} overflow-hidden h-dvh`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
