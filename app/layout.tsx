import type { Metadata } from "next";
import { ThemeProvider } from "@/components/navigation/theme-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gauntlet",
  description: "AI Certification Prep App",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
