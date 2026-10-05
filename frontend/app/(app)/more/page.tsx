"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, Sparkles, LogOut, Eye, Settings2, Palette } from "lucide-react";
import { Card } from "@/components/ui/card";
import { getUser, clearSession } from "@/lib/auth";

export default function More() {
  const router = useRouter();
  const user = getUser();
  const rows = [
    { href: "/catalogs", label: "Mis catálogos", icon: BookOpen },
    { href: "/settings/brand", label: "Ajustes de marca", icon: Palette },
    { href: "/products/review", label: "Revisar productos", icon: Settings2, Palette },
    { href: "/demo", label: "Ver catálogo de ejemplo", icon: Eye },
    ...(user?.is_admin ? [{ href: "/admin/ai", label: "Panel de IA", icon: Sparkles }] : []),
  ];
  return (
    <div className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-black">Más</h1>
      <p className="text-sm text-stone-500">{user?.name} · {user?.email}</p>
      <Card className="divide-y divide-stone-100 p-0">
        {rows.map(({ href, label, icon: I }) => (
          <Link key={href} href={href} className="flex items-center gap-3 px-4 py-4 text-sm font-medium"><I className="h-5 w-5 text-stone-500" />{label}</Link>
        ))}
        <button onClick={() => { clearSession(); router.replace("/login"); }} className="flex w-full items-center gap-3 px-4 py-4 text-sm font-medium text-red-600"><LogOut className="h-5 w-5" />Cerrar sesión</button>
      </Card>
    </div>
  );
}
