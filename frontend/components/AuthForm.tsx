"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { saveSession } from "@/lib/auth";
import { errMsg } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const isReg = mode === "register";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const r = isReg ? await api.register({ name, email, password }) : await api.login({ email, password });
      saveSession(r.access_token, r.user);
      const brands = await api.brands().catch(() => []);
      router.replace(brands.length ? "/dashboard" : "/onboarding");
    } catch (err) {
      setError(errMsg(err, isReg ? "No pudimos crear tu cuenta." : "Correo o contraseña incorrectos."));
    } finally { setBusy(false); }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-10">
      <Link href="/" className="mb-8 text-xl font-black tracking-tight">I2C</Link>
      <h1 className="text-3xl font-black tracking-tight">{isReg ? "Crea tu cuenta" : "Bienvenido de nuevo"}</h1>
      <form onSubmit={submit} className="mt-6 space-y-4">
        {isReg && (<div><Label>Tu nombre</Label><Input value={name} onChange={(e) => setName(e.target.value)} required autoComplete="name" /></div>)}
        <div><Label>Correo</Label><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" /></div>
        <div><Label>Contraseña</Label><Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={isReg ? 8 : 1} autoComplete={isReg ? "new-password" : "current-password"} />
          {isReg && <p className="mt-1 text-xs text-stone-400">Mínimo 8 caracteres</p>}</div>
        {error && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        <Button size="lg" className="w-full" disabled={busy}>{busy ? "Un momento..." : isReg ? "Crear cuenta" : "Entrar"}</Button>
      </form>
      <p className="mt-6 text-center text-sm text-stone-500">
        {isReg ? <>¿Ya tienes cuenta? <Link href="/login" className="font-semibold text-accent">Entrar</Link></> : <>¿Primera vez? <Link href="/register" className="font-semibold text-accent">Crear cuenta</Link></>}
      </p>
    </main>
  );
}
