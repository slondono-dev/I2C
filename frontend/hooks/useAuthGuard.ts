"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, getUser } from "@/lib/auth";
import type { User } from "@/lib/types";

export function useAuthGuard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    setUser(getUser()); setReady(true);
  }, [router]);
  return { user, ready };
}
