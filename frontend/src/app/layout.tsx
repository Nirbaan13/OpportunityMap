import type { Metadata } from "next";
import { Outfit, Syne } from "next/font/google";

import { AuthProvider } from "@/components/AuthProvider";
import { MobileBottomNav } from "@/components/MobileBottomNav";
import { SiteHeader } from "@/components/SiteHeader";

import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
});

export const metadata: Metadata = {
  title: "OpportunityMap",
  description:
    "Discover opportunities you are eligible for — olympiads, hackathons, research programs, and more.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${syne.variable} antialiased`}>
        <AuthProvider>
          <SiteHeader />
          <div className="pb-[calc(3.25rem+env(safe-area-inset-bottom))] md:pb-0">{children}</div>
          <MobileBottomNav />
        </AuthProvider>
      </body>
    </html>
  );
}
