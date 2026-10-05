import type { User } from "./types";

const TOKEN = "i2c_token";
const USER = "i2c_user";

export function getToken(): string | null {
  try { return typeof window === "undefined" ? null : localStorage.getItem(TOKEN); } catch { return null; }
}
export function getUser(): User | null {
  try {
    const raw = typeof window === "undefined" ? null : localStorage.getItem(USER);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch { return null; }
}
export function saveSession(token: string, user: User) {
  try { localStorage.setItem(TOKEN, token); localStorage.setItem(USER, JSON.stringify(user)); } catch { /* ignore */ }
}
export function clearSession() {
  try { localStorage.removeItem(TOKEN); localStorage.removeItem(USER); } catch { /* ignore */ }
}
