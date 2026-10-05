import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { fetchPublicCatalog } from "@/lib/api";
import { ProductView } from "@/components/catalog/ProductView";
import { themeStyle } from "@/components/catalog/CatalogRenderer";

export const dynamic = "force-dynamic";
type P = { params: Promise<{ slug: string; id: string }> };

export default async function PublicProductPage({ params }: P) {
  const { slug, id } = await params;
  const c = await fetchPublicCatalog(slug);
  const p = c?.products.find((x) => x.id === id);
  if (!c || !p) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 text-center">
        <h1 className="text-2xl font-black">Producto no encontrado</h1>
        <Link href={`/c/${slug}`} className="mt-4 underline">Ver catálogo</Link>
      </main>
    );
  }
  return (
    <div className="min-h-screen px-4 py-6" style={themeStyle(c.theme, c.brand.primary_color)}>
      <Link href={`/c/${slug}`} className="mx-auto mb-4 flex max-w-4xl items-center gap-2 text-sm opacity-70"><ArrowLeft className="h-4 w-4" /> {c.brand.name}</Link>
      <ProductView product={p} theme={c.theme} shareUrl={`/c/${slug}/p/${id}`} />
    </div>
  );
}
