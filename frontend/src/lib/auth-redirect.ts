/** Safe in-app redirect path from `?next=` (blocks open redirects). */
export function safeNextPath(raw: string | null | undefined, fallback = "/profile"): string {
  if (!raw) return fallback;
  let value = raw.trim();
  try {
    value = decodeURIComponent(value);
  } catch {
    return fallback;
  }
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("://")) {
    return fallback;
  }
  return value;
}

export function loginHref(next?: string | null): string {
  if (!next) return "/login";
  const path = safeNextPath(next, "");
  if (!path) return "/login";
  return `/login?next=${encodeURIComponent(path)}`;
}
