import type { ThemeName } from "@/lib/types";

export type ThemeConfig = {
  accent: string; bg: string; fg: string; muted: string; cardBg: string; border: string;
  font: string; headingFont: string; headingClass: string; brandClass: string;
  gridClass: string; cardClass: string; aspect: string; imgClass: string; nameClass: string; priceClass: string;
  stagger: number; hover: number; headerAlign: string;
};

const sans = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
const serif = 'ui-serif, Georgia, Cambria, "Times New Roman", serif';

export const THEMES: Record<ThemeName, ThemeConfig> = {
  minimal: {
    accent: "#18181b", bg: "#ffffff", fg: "#18181b", muted: "#71717a", cardBg: "#fafafa", border: "#e4e4e7",
    font: sans, headingFont: sans, headingClass: "text-3xl font-semibold tracking-tight", brandClass: "text-lg font-semibold tracking-tight",
    gridClass: "grid-cols-2 gap-x-3 gap-y-8 md:grid-cols-3 lg:grid-cols-4 md:gap-x-5", cardClass: "", aspect: "aspect-[3/4]",
    imgClass: "rounded-xl", nameClass: "text-sm font-medium", priceClass: "text-sm text-[color:var(--muted)]", stagger: 0.05, hover: 1.05, headerAlign: "text-left",
  },
  editorial: {
    accent: "#8a5a3c", bg: "#f6f1e9", fg: "#2b2118", muted: "#7a6a5a", cardBg: "#efe7da", border: "#dccfbb",
    font: serif, headingFont: serif, headingClass: "text-5xl italic font-normal leading-none", brandClass: "text-xl uppercase tracking-[0.3em]",
    gridClass: "grid-cols-1 gap-y-14 sm:grid-cols-2 gap-x-8 lg:grid-cols-3", cardClass: "", aspect: "aspect-[4/5]",
    imgClass: "rounded-none", nameClass: "text-xl italic", priceClass: "text-sm tracking-widest uppercase text-[color:var(--muted)]", stagger: 0.08, hover: 1.04, headerAlign: "text-center",
  },
  street: {
    accent: "#d4ff1f", bg: "#0b0b0b", fg: "#f5f5f5", muted: "#a3a3a3", cardBg: "#171717", border: "#262626",
    font: sans, headingFont: 'Impact, "Arial Narrow Bold", sans-serif', headingClass: "text-6xl uppercase font-black leading-[0.9] tracking-tight", brandClass: "text-xl font-black uppercase tracking-tighter",
    gridClass: "grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-4", cardClass: "overflow-hidden", aspect: "aspect-square",
    imgClass: "rounded-none", nameClass: "text-sm font-black uppercase", priceClass: "text-sm font-bold text-[color:var(--accent)]", stagger: 0.04, hover: 1.1, headerAlign: "text-left",
  },
  premium: {
    accent: "#c9a44c", bg: "#0f0d0b", fg: "#f1ebe0", muted: "#9c9283", cardBg: "#1a1714", border: "#2e2923",
    font: serif, headingFont: serif, headingClass: "text-4xl font-light tracking-wide", brandClass: "text-lg uppercase tracking-[0.4em] font-light",
    gridClass: "grid-cols-2 gap-x-4 gap-y-10 md:grid-cols-3", cardClass: "", aspect: "aspect-[3/4]",
    imgClass: "rounded-sm ring-1 ring-[color:var(--border)]", nameClass: "text-sm tracking-wide", priceClass: "text-sm text-[color:var(--accent)]", stagger: 0.07, hover: 1.03, headerAlign: "text-center",
  },
  colorful: {
    accent: "#7c3aed", bg: "#fff4fa", fg: "#2e1065", muted: "#8b5cf6", cardBg: "#ffffff", border: "#f5d0fe",
    font: 'ui-rounded, "Nunito", ' + sans, headingFont: 'ui-rounded, ' + sans, headingClass: "text-4xl font-black tracking-tight", brandClass: "text-xl font-black",
    gridClass: "grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4", cardClass: "rounded-3xl p-2 shadow-lg shadow-fuchsia-200/50 bg-[color:var(--cardBg)]", aspect: "aspect-[4/5]",
    imgClass: "rounded-2xl", nameClass: "text-sm font-bold", priceClass: "text-sm font-black text-[color:var(--accent)]", stagger: 0.06, hover: 1.08, headerAlign: "text-left",
  },
};
