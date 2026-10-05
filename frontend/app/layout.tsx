import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";
import { RegisterSW } from "@/components/RegisterSW";

export const metadata: Metadata = {
  title: "I2C — Catálogo desde fotos",
  description: "Fotografía tus productos y conviértelos automáticamente en un catálogo listo para vender.",
  manifest: "/manifest.json",
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
  appleWebApp: { capable: true, title: "I2C", statusBarStyle: "default" },
};
export const viewport: Viewport = { themeColor: "#4f46e5", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <ToastProvider>{children}</ToastProvider>
        <RegisterSW />
      </body>
    </html>
  );
}
