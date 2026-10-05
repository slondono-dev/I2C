"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Brand, Catalog } from "@/lib/types";

export function useWorkspace() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const b = await api.brands();
      const c = (await Promise.all(b.map((x) => api.catalogs(x.id)))).flat();
      setBrands(b); setCatalogs(c); setError(null);
    } catch (e) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { reload(); }, [reload]);

  const catalog = catalogs[0] ?? null;
  const brand = brands.find((b) => b.id === catalog?.brand_id) ?? brands[0] ?? null;
  return { brands, catalogs, catalog, brand, loading, error, reload, setCatalogs };
}
