import type { Metadata } from "next";
import { fetchPublicCatalog } from "@/lib/api";
import { CatalogRenderer } from "@/components/catalog/CatalogRenderer";

export const dynamic = "force-dynamic";
type P = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: P): Promise<Metadata> {
  const { slug } = await params;
  const c = await fetchPublicCatalog(slug);
  return c ? { title: `${c.name} — ${c.brand.name}`, description: c.description ?? "Catálogo" } : { title: "Catálogo" };
}

export default async function PublicCatalogPage({ params }: P) {
  const { slug } = await params;
  const c = await fetchPublicCatalog(slug);
  if (!c) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
        <h1 className="text-2xl font-black">Este catálogo aún no está disponible</h1>
        <p className="mt-2 text-stone-500">Puede que no se haya publicado todavía. Vuelve a intentarlo más tarde.</p>
      </main>
    );
  }
  return <CatalogRenderer catalog={c} products={c.products} theme={c.theme} />;
}
