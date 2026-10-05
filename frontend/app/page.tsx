import Link from "next/link";
import { Camera, Sparkles, MessageCircle } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Landing() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-between px-6 py-10">
      <div className="text-xl font-black tracking-tight">I2C</div>
      <section>
        <h1 className="text-4xl font-black leading-tight tracking-tight">
          Fotografía tus productos y conviértelos en un catálogo listo para vender.
        </h1>
        <p className="mt-4 text-stone-500">Toma la foto. La IA hace el resto. Comparte el link y recibe pedidos por WhatsApp.</p>
        <ul className="mt-8 space-y-3 text-sm text-stone-700">
          <li className="flex items-center gap-3"><Camera className="h-5 w-5 text-accent" /> Foto desde tu celular</li>
          <li className="flex items-center gap-3"><Sparkles className="h-5 w-5 text-accent" /> Nombre, descripción y fondo limpio automáticos</li>
          <li className="flex items-center gap-3"><MessageCircle className="h-5 w-5 text-accent" /> Pedidos directo a tu WhatsApp</li>
        </ul>
      </section>
      <div className="space-y-3">
        <Link href="/register" className={cn(buttonVariants({ size: "xl" }), "w-full")}>Empezar</Link>
        <Link href="/login" className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}>Entrar</Link>
        <Link href="/demo" className="block pt-2 text-center text-sm text-stone-500 underline">Ver catálogo de ejemplo</Link>
      </div>
    </main>
  );
}
