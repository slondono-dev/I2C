import * as React from "react";
import { cn } from "@/lib/utils";
export function Card({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-3xl border border-stone-200 bg-white p-4 shadow-sm", className)} {...p} />;
}
