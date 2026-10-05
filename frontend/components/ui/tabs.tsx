"use client";
import { cn } from "@/lib/utils";
export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: { value: T; label: string }[] }) {
  return (
    <div className="inline-flex rounded-xl bg-stone-100 p-1">
      {items.map((i) => (
        <button key={i.value} onClick={() => onChange(i.value)}
          className={cn("rounded-lg px-3 py-1.5 text-sm font-medium transition", value === i.value ? "bg-white shadow-sm text-stone-900" : "text-stone-500")}>
          {i.label}
        </button>
      ))}
    </div>
  );
}
