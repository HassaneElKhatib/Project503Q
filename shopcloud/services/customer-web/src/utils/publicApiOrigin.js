export function publicApiOrigin() {
  const v = import.meta.env.VITE_BACKEND_URL;
  if (v === undefined || v === null) return "";
  return String(v).trim().replace(/\/$/, "");
}

export function publicApiBase() {
  const o = publicApiOrigin();
  return o ? `${o}/api` : "/api";
}
