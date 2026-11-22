import type { Metadata, Viewport } from "next";
import { Anton, DM_Sans } from "next/font/google";
import "./globals.css";
import "./wow.css";

const anton = Anton({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-anton",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BillBack: you may not owe this bill",
  description:
    "Add a photo of a hospital bill, answer two questions, and see if you likely qualify for free or discounted care. Likely eligible, not a guarantee.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#CFEFE0" },
    { media: "(prefers-color-scheme: dark)", color: "#0D2C24" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${anton.variable} ${dmSans.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
