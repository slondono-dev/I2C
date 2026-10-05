"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Home, Package, Plus, BookOpen, Menu } from "lucide-react";
import { useAuthGuard } from "@/hooks/useAuthGuard";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { clearSession } from "@/lib/auth";

const items = [
  { href: "/dashboard", label: "Inicio", icon: Home },
  { href: "/products", label: "Productos", icon: Package },
  { href: "/products/new", label: "Agregar", icon: Plus, main: true },
  { href: "/catalogs", label: "Catálogo", icon: BookOpen },
  { href: "/more", label: "Más", icon: Menu },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { ready, user } = useAuthGuard();
  const path = usePathname();
  const router = useRouter();
  const active = (h: string) => (h === "/products" ? path === "/products" || (path.startsWith("/products/") && !path.startsWith("/products/new")) : path.startsWith(h));

  if (!ready) return <div className="mx-auto max-w-md space-y-4 p-6"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-40" /><Skeleton className="h-16" /></div>;

  return (
    <div className="min-h-screen pb-24 md:pb-8">
      <header className="sticky top-0 z-30 hidden border-b border-stone-200 bg-white/90 backdrop-blur md:block">
        <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-3">
          <Link href="/dashboard" className="text-lg font-black tracking-tight">I2C</Link>
          <nav className="flex gap-1">
            {items.filter((i) => !i.main).map((i) => (
              <Link key={i.href} href={i.href} className={cn("rounded-xl px-3 py-2 text-sm font-medium", active(i.href) ? "bg-stone-100" : "text-stone-500 hover:bg-stone-50")}>{i.label}</Link>
            ))}
          </nav>
          <Link href="/products/new" className="ml-auto rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">+ Agregar productos</Link>
          {user?.is_admin && <Link href="/admin/ai" className="text-sm text-stone-500">IA</Link>}
          <button className="text-sm text-stone-500" onClick={() => { clearSession(); router.replace("/login"); }}>Salir</button>
        </div>
      </header>
      <div className="mx-auto max-w-5xl px-4 py-5 md:px-6">{children}</div>
      <nav className="pb-safe fixed inset-x-0 bottom-0 z-30 border-t border-stone-200 bg-white/95 backdrop-blur md:hidden" aria-label="Principal">
        <ul className="mx-auto grid max-w-md grid-cols-5 items-end px-2 pt-1.5">
          {items.map(({ href, label, icon: Icon, main }) => (
            <li key={href} className="flex justify-center">
              <Link href={href} className={cn("flex flex-col items-center gap-0.5 text-[11px] font-medium", main ? "-mt-5" : "py-1", !main && (active(href) ? "text-accent" : "text-stone-500"))}>
                {main ? (
                  <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent text-white shadow-lg shadow-indigo-300"><Icon className="h-7 w-7" /></span>
                ) : <Icon className="h-6 w-6" />}
                <span className={main ? "text-accent" : ""}>{label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
