import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { Providers } from "@/components/Providers";
import "./globals.css";
import "./intel.css";

export const metadata: Metadata = {
  title: "Lead Engine",
  description: "Autonomous local business intelligence",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent" },
};

export const viewport: Viewport = {
  themeColor: "#060606",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={GeistSans.variable}>
      <body className={`min-h-screen antialiased ${GeistSans.className}`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
