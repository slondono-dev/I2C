"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Camera } from "lucide-react";
import { api } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { useWorkspace } from "@/hooks/useWorkspace";
import { CatalogCard } from "@/components/CatalogCard";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/types";

export default function Dashboard() {
  const router = useRouter();
  const ws = useWorkspace();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [low, setLow] = useState<number | null>(null);
  const user = getUser();
  const { catalog, loading, brands } = ws;

  useEffect(() => { if (!loading && brands.length === 0 && !ws.error) router.replace("/onboarding"); }, [loading, brands, ws.error, router]);
  useEffect(() => {
    if (!catalog) return;
    api.products({ catalog_id: catalog.id }).then(setProducts).catch(() => setProducts([]));
    api.products({ catalog_id: catalog.id, low_stock: 5 }).then((l) => setLow(l.length)).catch(() => setLow(0));
  }, [catalog]);

  const published = products?.filter((p) => p.status === "published").length;
  const stats = [
    { label: "Productos", v: products?.length },
    { label: "Stock bajo", v: low ?? undefined },
    { label: "Publicados", v: published },
  ];

  return (
    <div className="mx-auto max-w-md space-y-5">
      <h1 className="text-3xl font-black tracking-tight">Hola, {user?.name?.split(" ")[0] ?? ""} 👋</h1>
      {loading ? <Skeleton className="h-56" /> : ws.error ? (
        <Card className="text-sm text-red-700">No pudimos cargar tu información. Revisa tu conexión e inténtalo de nuevo.</Card>
      ) : catalog ? (
        <CatalogCard catalog={catalog} onChange={(c) => ws.setCatalogs((s) => s.map((x) => (x.id === c.id ? c : x)))} />
      ) : <Skeleton className="h-56" />}
      <Link href="/products/new" className={cn(buttonVariants({ size: "xl" }), "w-full gap-3 text-base shadow-lg shadow-indigo-200")}>
        <Camera className="h-6 w-6" /> + AGREGAR PRODUCTOS
      </Link>
      <Link href="/settings/brand" className="block text-center text-sm font-medium text-accent underline">Ajustes de marca</Link>
      <div className="grid grid-cols-3 gap-3">
        {stats.map((s) => (
          <Card key={s.label} className="p-3 text-center">
            {s.v === undefined ? <Skeleton className="mx-auto h-8 w-10" /> : <div className="text-2xl font-black">{s.v}</div>}
            <div className="text-xs text-stone-500">{s.label}</div>
          </Card>
        ))}
      </div>
    </div>
  );
}
