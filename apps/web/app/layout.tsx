import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { MobileTabBar } from "@/components/mobile-tab-bar";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "light-event — персонал для событий",
  description:
    "light-event соединяет отели, рестораны и кейтеринг с проверенными временными сотрудниками.",
  // PWA (§11.13): установка на главный экран iOS/Android
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "light-event",
  },
  icons: {
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#16a34a",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover", // нижний таб-бар учитывает safe-area iPhone
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      className={`${GeistSans.variable} ${GeistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          {children}
          <MobileTabBar />
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
